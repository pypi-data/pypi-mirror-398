# Z85base91 - Base91 and Z85 Encodings

This repository provides C and Python implementations of three encoding schemes: **Z85P**, **Base91**, and **Z85B**.

The C-based shared libraries are optimized for performance, while Python implementations provide a fallback when the C
libraries are not available.

The repository contains:

- **Base91 encoding**: A binary-to-text encoding scheme that uses 91 printable ASCII characters.
- **Z85B encoding**: A variant of Z85 used for efficient binary-to-text encoding.
- **Z85P encoding**: Another variant of Z85, with different padding scheme.

## Features

- **C-based implementation** for each encoding scheme for maximum performance.
- **Pure Python fallback** for environments where the C libraries are not available.
- Easy-to-use API for encoding and decoding with detailed error handling and logging.
- Cross-platform support (Linux, macOS, Windows) via system architecture detection.

## Benchmarks

| Encoding                                                                                                               | Avg Encoding Time (ns) | Avg Decoding Time (ns) | Avg Size Increase | Encoding Rank | Decoding Rank | Size Increase Rank |
|------------------------------------------------------------------------------------------------------------------------|------------------------|------------------------|-------------------|---------------|---------------|--------------------|
| [pybase64](https://github.com/mayeut/pybase64)                                                                         | 1131 ns                | 2946 ns                | 1.35x             | 1 🥇          | 1 🥇          | 4                  |
| **base91**                                                                                                             | 622324 ns              | 38632 ns               | 1.23x             | 5             | 4             | 1 🥇               |
| [base64](https://docs.python.org/3/library/base64.html)                                                                | 7113 ns                | 7051 ns                | 1.35x             | 3 🥉          | 3 🥉          | 4                  |
| [base16](https://docs.python.org/3/library/binascii.html)                                                              | 5953 ns                | 5859 ns                | 2.00x             | 2 🥈          | 2 🥈          | 6                  |
| **z85b**                                                                                                               | 626214 ns              | 871890 ns              | 1.25x             | 6             | 6             | 2 🥈               |
| **z85p**                                                                                                               | 633825 ns              | 775821 ns              | 1.28x             | 7             | 5             | 3 🥉               |
| [base32](https://docs.python.org/3/library/base64.html)                                                                | 503698 ns              | 882194 ns              | 1.62x             | 4             | 7             | 5                  |
| [z85p_py](https://github.com/JarbasHiveMind/hivemind-websocket-client/blob/dev/hivemind_bus_client/encodings/z85p.py)  | 940859 ns              | 1159043 ns             | 1.28x             | 8             | 8             | 3 🥉               |
| [z85b_py](https://github.com/JarbasHiveMind/hivemind-websocket-client/blob/dev/hivemind_bus_client/encodings/z85b.py)  | 983796 ns              | 1314734 ns             | 1.25x             | 9             | 9             | 2 🥈               |
| [base91_py](https://github.com/JarbasHiveMind/hivemind-websocket-client/blob/dev/hivemind_bus_client/encodings/b91.py) | 1414374 ns             | 2080957 ns             | 1.23x             | 10            | 10            | 1 🥇               |

## Usage

You can use the provided classes to encode and decode data using the supported encoding schemes.

### Z85P Encoding

```python
from z85p import Z85P

# Encode data
data = b"Hello, World!"
encoded = Z85P.encode(data)
print("Encoded Z85P:", encoded)

# Decode data
decoded = Z85P.decode(encoded)
print("Decoded Z85P:", decoded)
```

### Base91 Encoding

```python
from base91 import B91

# Encode data
data = b"Hello, World!"
encoded = B91.encode(data)
print("Encoded Base91:", encoded)

# Decode data
decoded = B91.decode(encoded)
print("Decoded Base91:", decoded)
```

### Z85B Encoding

```python
from z85b import Z85B

# Encode data
data = b"Hello, World!"
encoded = Z85B.encode(data)
print("Encoded Z85B:", encoded)

# Decode data
decoded = Z85B.decode(encoded)
print("Decoded Z85B:", decoded)
```

## Error Handling

The library automatically falls back to the Python implementation if the C libraries are not found or fail to load. Any
issues related to encoding or decoding will raise a `ValueError` with a detailed message.

In the case of missing C libraries, warnings will be logged using Python's built-in `logging` module.

### Logging

The library uses the `logging` module to provide useful runtime information:

```bash
2025-01-08 12:34:56,789 - WARNING - Z85P C library not available: Library load error. Falling back to pure Python implementation.
```
