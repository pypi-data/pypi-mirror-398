import ctypes
import logging
import os.path
import platform
from ctypes import c_char_p, c_void_p, c_size_t, c_ubyte, byref, POINTER
from typing import Union

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')


# get the appropriate shared library file based on architecture
def get_arch_lib(lib_base_name: str) -> str:
    """
    Returns the path to the shared library based on the system's architecture.

    Args:
        lib_base_name (str): The base name of the shared library (e.g., 'libz85p').

    Returns:
        str: The path to the shared library for the appropriate system architecture.

    Raises:
        ValueError: If the system architecture is unsupported.
    """
    arch = platform.machine()  # Get system architecture
    if arch == "x86_64":
        return f"{os.path.dirname(__file__)}/{lib_base_name}-x86_64.so"
    elif arch == "aarch64":
        return f"{os.path.dirname(__file__)}/{lib_base_name}-aarch64.so"
    elif arch == "i386" or arch == "i686":
        return f"{os.path.dirname(__file__)}/{lib_base_name}-i386.so"
    else:
        raise ValueError(f"Unsupported architecture: {arch}")


try:
    class Z85P:
        """
        Class for encoding and decoding Z85P format using a C-based shared library.
        If the C library is not available, it falls back to a pure Python implementation.
        """
        Z85CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-:+=^!/*?&<>()[]{}@%$#"

        # Load the correct shared library based on system architecture
        lib = ctypes.CDLL(get_arch_lib('libz85p'))

        # Initialize the Z85 map (this needs to be called first)
        lib.initialize_z85_map()

        # Define the encode function prototype
        lib.encode_z85p.argtypes = [ctypes.POINTER(ctypes.c_ubyte), c_size_t, POINTER(c_size_t)]
        lib.encode_z85p.restype = ctypes.POINTER(ctypes.c_ubyte)

        # Define the decode function prototype
        lib.decode_z85p.argtypes = [ctypes.POINTER(ctypes.c_ubyte), c_size_t, POINTER(c_size_t)]
        lib.decode_z85p.restype = ctypes.POINTER(ctypes.c_ubyte)

        @classmethod
        def encode(cls, data: Union[str, bytes]) -> bytes:
            """
            Encodes the input data into Z85P format.

            Args:
                data (bytes): The raw data to encode.

            Returns:
                bytes: The Z85P-encoded data.

            Raises:
                ValueError: If encoding fails.
            """
            if isinstance(data, str):
                data = data.encode('utf-8')

            out_len = c_size_t(0)
            raw_data = (ctypes.c_ubyte * len(data))(*data)
            encoded_data = cls.lib.encode_z85p(raw_data, len(data), ctypes.byref(out_len))
            return bytes(ctypes.string_at(encoded_data, out_len.value))

        @classmethod
        def decode(cls, encoded_data: Union[str, bytes]) -> bytes:
            """
            Decodes the input Z85P-encoded data into raw bytes.

            Args:
                encoded_data (bytes): The Z85P-encoded data to decode.

            Returns:
                bytes: The decoded raw data.

            Raises:
                ValueError: If decoding fails.
            """
            if isinstance(encoded_data, str):
                if any(c not in Z85P.Z85CHARS for c in encoded_data):
                    raise ValueError("Invalid Z85 character")
                encoded_data = encoded_data.encode('utf-8')

            out_len = c_size_t(0)
            raw_data = (ctypes.c_ubyte * len(encoded_data))(*encoded_data)
            decoded_data = cls.lib.decode_z85p(raw_data, len(encoded_data), ctypes.byref(out_len))
            return bytes(ctypes.string_at(decoded_data, out_len.value))
except Exception as e:
    logging.warning(f"Z85P C library not available: {e}. Falling back to pure Python implementation.")
    from z85base91.z85p import Z85P

try:
    class B91:
        """
        Class for encoding and decoding Base91 format using a C-based shared library.
        If the C library is not available, it falls back to a pure Python implementation.
        """
        # Load the correct shared library based on system architecture
        lib = ctypes.CDLL(get_arch_lib('libbase91'))

        # Initialize the decode table (this needs to be called first)
        lib.initialize_decode_table()

        # Define the decode function prototype
        lib.decode.argtypes = [c_char_p, ctypes.POINTER(c_size_t)]
        lib.decode.restype = c_void_p

        # Define the encode function prototype
        lib.encode.argtypes = [ctypes.POINTER(ctypes.c_ubyte), c_size_t, ctypes.POINTER(c_size_t)]
        lib.encode.restype = c_char_p

        @classmethod
        def encode(cls, data: Union[str, bytes]) -> bytes:
            """
            Encodes the input data into Base91 format.

            Args:
                data (Union[str, bytes]): The raw data to encode.

            Returns:
                bytes: The Base91-encoded data.

            Raises:
                ValueError: If encoding fails.
            """
            if isinstance(data, str):
                # Convert the data to bytes
                data = data.encode('utf-8')
            output_len = c_size_t(0)

            # Call the C function
            encoded_data = cls.lib.encode((ctypes.c_ubyte * len(data))(*data), len(data), ctypes.byref(output_len))

            return ctypes.string_at(encoded_data, output_len.value)

        @classmethod
        def decode(cls, encoded_data: Union[str, bytes]) -> bytes:
            """
            Decodes the input Base91-encoded data into raw bytes.

            Args:
                encoded_data (Union[str, bytes]): The Base91-encoded data to decode.

            Returns:
                bytes: The decoded raw data.

            Raises:
                ValueError: If decoding fails.
            """
            if isinstance(encoded_data, str):
                # Convert the encoded data to bytes
                encoded_data = encoded_data.encode('utf-8')
            output_len = c_size_t(0)

            # Call the C function
            decoded_data = cls.lib.decode(encoded_data, ctypes.byref(output_len))

            if not decoded_data:
                raise ValueError("Invalid Base91 string")
            return ctypes.string_at(decoded_data, output_len.value)

except Exception as e:
    logging.warning(f"Base91 C library not available: {e}. Falling back to pure Python implementation.")
    from z85base91.b91 import B91

try:
    class Z85B:
        """
        Class for encoding and decoding Z85B format using a C-based shared library.
        If the C library is not available, it falls back to a pure Python implementation.
        """
        # Load the correct shared library based on system architecture
        lib = ctypes.CDLL(get_arch_lib('libz85b'))

        # Define function prototypes
        lib.encode_z85b.argtypes = [POINTER(c_ubyte), c_size_t, POINTER(c_size_t)]
        lib.encode_z85b.restype = POINTER(c_ubyte)

        lib.decode_z85b.argtypes = [POINTER(c_ubyte), c_size_t, POINTER(c_size_t)]
        lib.decode_z85b.restype = POINTER(c_ubyte)

        lib.free.argtypes = [ctypes.c_void_p]  # Add free function for memory cleanup

        @classmethod
        def encode(cls, data: Union[str, bytes]) -> bytes:
            """
            Encodes the input data into Z85B format.

            Args:
                data (bytes): The raw data to encode.

            Returns:
                bytes: The Z85B-encoded data.

            Raises:
                ValueError: If encoding fails.
            """
            if isinstance(data, str):
                data = data.encode('utf-8')
            output_len = c_size_t(0)
            encoded_data = cls.lib.encode_z85b((c_ubyte * len(data))(*data), len(data), byref(output_len))
            if not encoded_data:
                raise ValueError("Encoding failed")

            try:
                return ctypes.string_at(encoded_data, output_len.value)
            finally:
                cls.lib.free(encoded_data)

        @classmethod
        def decode(cls, encoded_data: Union[str, bytes]) -> bytes:
            """
            Decodes the input Z85B-encoded data into raw bytes.

            Args:
                encoded_data (bytes): The Z85B-encoded data to decode.

            Returns:
                bytes: The decoded raw data.

            Raises:
                ValueError: If decoding fails.
            """
            if isinstance(encoded_data, str):
                # Convert the encoded data to bytes
                if any(c not in Z85P.Z85CHARS for c in encoded_data):
                    raise ValueError("Invalid Z85 character")
                encoded_data = encoded_data.encode('utf-8')
            output_len = c_size_t(0)
            decoded_data = cls.lib.decode_z85b((c_ubyte * len(encoded_data))(*encoded_data), len(encoded_data),
                                               byref(output_len))
            try:
                return ctypes.string_at(decoded_data, output_len.value)
            finally:
                cls.lib.free(decoded_data)
except Exception as e:
    logging.warning(f"Z85B C library not available: {e}. Falling back to pure Python implementation.")
    from z85base91.z85b import Z85B

if __name__ == "__main__":

    from z85base91.b91 import B91 as B91py
    from z85base91.z85b import Z85B as Z85Bpy
    from z85base91.z85p import Z85P as Z85Ppy


    def test_b91(s=b"Hello, Base91!"):
        # Example usage:
        try:
            pencoded = B91py.encode(s)
            print("Encoded py:", pencoded)
            pdecoded = B91py.decode(pencoded)
            print("Decoded py:", pdecoded)

            encoded = B91.encode(s)
            print("Encoded:", encoded)
            decoded = B91.decode(encoded)
            print("Decoded:", decoded)

            assert pdecoded == decoded
            assert pencoded == encoded
        except Exception as e:
            print(f"Error: {e}")


    def test_z85b(s=b"Hello, Z85B!"):
        try:
            pencoded = Z85Bpy.encode(s)
            print("Encoded py:", pencoded)
            pdecoded = Z85Bpy.decode(pencoded)
            print("Decoded py:", pdecoded)

            encoded = Z85B.encode(s)
            print("Encoded:", encoded)
            decoded = Z85B.decode(encoded)
            print("Decoded:", decoded)

            assert pdecoded == decoded
            assert pencoded == encoded
        except Exception as e:
            print(f"Error: {e}")


    def test_z85p(s=b"Hello, Z85P!"):
        try:
            pencoded = Z85Ppy.encode(s)
            print(f"Encoded py: {pencoded}")
            pdecoded = Z85Ppy.decode(pencoded)
            print(f"Decoded py: {pdecoded.decode('utf-8')}")

            encoded = Z85P.encode(s)
            print(f"Encoded: {encoded}")
            decoded = Z85P.decode(encoded)
            print(f"Decoded: {decoded.decode('utf-8')}")

            assert pdecoded == decoded
            assert pencoded == encoded
        except Exception as e:
            print(f"Error: {e}")


    test_b91()
    test_z85p()
    test_z85b()
