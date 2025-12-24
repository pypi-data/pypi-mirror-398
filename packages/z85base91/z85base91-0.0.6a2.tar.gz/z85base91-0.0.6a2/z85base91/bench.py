import base64
import pybase64
import random
import string
import time
from typing import Callable, Dict, List, Tuple

import click
from z85base91 import Z85P, Z85B, B91
from hivemind_bus_client.encodings import Z85B as Z85Bpy, Z85P as Z85Ppy, B91 as B91py
from tabulate import tabulate


def get_encoder(encoding: str) -> Callable[[bytes], bytes]:
    """Retrieve the encoder function for the given encoding."""
    encoders = {
        "base64": base64.b64encode,
        "base64_py": pybase64.b64encode,
        "z85b": Z85B.encode,
        "z85p": Z85P.encode,
        "base91": B91.encode,
        "z85b_py": Z85Bpy.encode,
        "z85p_py": Z85Ppy.encode,
        "base91_py": B91py.encode,
        "base32": base64.b32encode
    }
    return encoders[encoding]


def get_decoder(encoding: str) -> Callable[[bytes], bytes]:
    """Retrieve the decoder function for the given encoding."""
    decoders = {
        "base64": base64.b64decode,
        "base64_py": pybase64.b64decode,
        "z85b": Z85B.decode,
        "z85p": Z85P.decode,
        "base91": B91.decode,
        "z85b_py": Z85Bpy.decode,
        "z85p_py": Z85Ppy.decode,
        "base91_py": B91py.decode,
        "base32": base64.b32decode
    }
    return decoders[encoding]


def generate_random_data(size: int) -> bytes:
    """Generate random binary data of a given size."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode("utf-8")


def benchmark_encoding(encoding: str, data: bytes) -> Dict[str, int]:
    """Benchmark encoding and decoding for a given encoding."""
    encoder = get_encoder(encoding)
    decoder = get_decoder(encoding)

    # Measure encoding time in nanoseconds
    start_time = time.perf_counter_ns()
    encoded_data = encoder(data)
    encoding_time = time.perf_counter_ns() - start_time

    # Measure decoding time in nanoseconds
    start_time = time.perf_counter_ns()
    decoded_data = decoder(encoded_data)
    decoding_time = time.perf_counter_ns() - start_time

    # Validate decoding
    if decoded_data != data:
        raise ValueError(f"Decoded data does not match for encoding {encoding}.")

    # Calculate size increase
    original_size = len(data)
    encoded_size = len(encoded_data)
    size_increase = encoded_size / original_size

    return {
        "encoding_time": encoding_time,
        "decoding_time": decoding_time,
        "size_increase": size_increase,
    }


def get_rankings(metric: Dict[str, Dict[str, int]], key: str) -> List[Tuple[str, int]]:
    """Rank the encodings based on the provided metric, handling ties."""
    sorted_encodings = sorted(metric.items(), key=lambda x: x[1][key], reverse=False)
    rankings = []
    current_rank = 1  # Start from rank 1

    for i in range(len(sorted_encodings)):
        if i > 0 and sorted_encodings[i][1][key] == sorted_encodings[i - 1][1][key]:
            # Tie case: Same rank as the previous item
            rankings.append((sorted_encodings[i][0], rankings[-1][1]))
        else:
            # No tie, increase the rank
            rankings.append((sorted_encodings[i][0], current_rank))
            current_rank += 1  # Increment rank only when no tie

    return rankings


def compare_python_c(encoding: str, python_results: Dict[str, Dict[str, int]],
                     c_results: Dict[str, Dict[str, int]]) -> float:
    """Compare the speed between Python and C encodings and calculate how many times faster or slower it is."""
    if encoding.endswith("_py"):
        c_encoding = encoding[:-3]  # Remove the _py suffix to get the C counterpart
        python_time = python_results[encoding]["encoding_time"]
        c_time = c_results[c_encoding]["encoding_time"]

        if c_time == 0:
            return float('inf')  # Avoid division by zero
        return python_time / c_time
    return 1.0  # If not a Python version, return 1 (no comparison)


@click.command()
@click.option("--sizes", default="100,1000,10000", help="Comma-separated list of data sizes to test.")
@click.option("--iterations", default=10, help="Number of iterations for each test.")
def main(sizes: str, iterations: int):
    sizes = list(map(int, sizes.split(",")))

    encodings = [
        "base64",
        "base32",
        "base64_py",
        "z85b",
        "z85p",
        "base91",
        "z85b_py",
        "z85p_py",
        "base91_py",
    ]

    results = {size: {encoding: [] for encoding in encodings} for size in sizes}

    # Run benchmarks
    for size in sizes:
        print(f"Testing size: {size} bytes")
        for _ in range(iterations):
            data = generate_random_data(size)
            for encoding in encodings:
                result = benchmark_encoding(encoding, data)
                results[size][encoding].append(result)

    # Calculate averages and print results
    global_ranking = {encoding: {"encoding_time": 0, "decoding_time": 0, "size_increase": 0} for encoding in encodings}
    table = []

    # Aggregate results across all sizes
    for encoding in encodings:
        total_encoding_time = 0
        total_decoding_time = 0
        total_size_increase = 0

        for size, encoding_results in results.items():
            avg_encoding_time = sum(m["encoding_time"] for m in encoding_results[encoding]) // iterations
            avg_decoding_time = sum(m["decoding_time"] for m in encoding_results[encoding]) // iterations
            avg_size_increase = sum(m["size_increase"] for m in encoding_results[encoding]) / iterations

            total_encoding_time += avg_encoding_time
            total_decoding_time += avg_decoding_time
            total_size_increase += avg_size_increase

            table.append([
                encoding,
                f"{avg_encoding_time} ns",
                f"{avg_decoding_time} ns",
                f"{avg_size_increase:.2f}x size increase"
            ])

        # Store global averages
        global_ranking[encoding]["encoding_time"] = total_encoding_time // len(sizes)
        global_ranking[encoding]["decoding_time"] = total_decoding_time // len(sizes)
        global_ranking[encoding]["size_increase"] = total_size_increase / len(sizes)

    # Global ranking (based on average times)
    print("\n### Global Ranking (Merged) ###")

    # Get rankings for encoding time, decoding time, and size increase
    sorted_by_encoding_time = get_rankings(global_ranking, "encoding_time")
    sorted_by_decoding_time = get_rankings(global_ranking, "decoding_time")
    sorted_by_size_increase = get_rankings(global_ranking, "size_increase")

    merged_table = []
    for encoding, metrics in global_ranking.items():
        encoding_time_rank = next(rank for enc, rank in sorted_by_encoding_time if enc == encoding)
        decoding_time_rank = next(rank for enc, rank in sorted_by_decoding_time if enc == encoding)
        size_increase_rank = next(rank for enc, rank in sorted_by_size_increase if enc == encoding)

        # Calculate the average rank
        avg_rank = (encoding_time_rank + decoding_time_rank + size_increase_rank) / 3

        # Medal assignments
        encoding_time_medal = "🥇" if encoding_time_rank == 1 else "🥈" if encoding_time_rank == 2 else "🥉" if encoding_time_rank == 3 else ""
        decoding_time_medal = "🥇" if decoding_time_rank == 1 else "🥈" if decoding_time_rank == 2 else "🥉" if decoding_time_rank == 3 else ""
        size_increase_medal = "🥇" if size_increase_rank == 1 else "🥈" if size_increase_rank == 2 else "🥉" if size_increase_rank == 3 else ""

        # Add the top-ranked emojis
        merged_table.append([
            encoding,
            f"{metrics['encoding_time']} ns",
            f"{metrics['decoding_time']} ns",
            f"{metrics['size_increase']:.2f}x",
            f"{encoding_time_rank} {encoding_time_medal}",
            f"{decoding_time_rank} {decoding_time_medal}",
            f"{size_increase_rank} {size_increase_medal}",
            avg_rank
        ])

        # Pairwise comparison for Python vs C
        if encoding.endswith("_py"):  # If it's a Python version
            speed_comparison = compare_python_c(encoding, global_ranking, global_ranking)
            if float(speed_comparison) > 1:
                merged_table[-1].append(f"{speed_comparison:.2f}x slower")
            else:
                merged_table[-1].append(f"{1/speed_comparison:.2f}x faster")

    # Sort the merged table based on the average rank
    merged_table.sort(key=lambda x: float(str(x[-2]).split()[0]), reverse=False)

    # Display the final table
    print(tabulate(merged_table,
                   headers=["Encoding", "Avg Encoding Time (ns)", "Avg Decoding Time (ns)", "Avg Size Increase",
                            "Encoding Rank", "Decoding Rank", "Size Increase Rank", "Score", "Reference vs Optimized"],
                   tablefmt="grid"))


if __name__ == "__main__":
    main()
