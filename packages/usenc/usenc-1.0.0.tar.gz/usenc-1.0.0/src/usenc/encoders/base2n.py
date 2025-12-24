from typing import Dict

from .encoder import DecodeError, EncodeError, Encoder


class Base2NEncoder(Encoder):
    """
    Base encoder for power-of-two base encodings (base64, base32, base16, etc.)

    This encoder works directly on bytes and returns bytes using bitwise operations.
    It supports various power-of-two bases where each encoded character represents
    a fixed number of bits (2, 3, 4, 5, 6, etc.).

    The encoder uses a custom alphabet and handles padding appropriately.
    """

    params = {
        "padding": {"nargs": "?", "const": "=", "help": "Specify the character used as padding"},
        "no_padding": {"action": "store_true", "help": "Do not include a padding character"},
        "alphabet": {
            "type": str,
            "default": None,
            "help": "Custom alphabet to use for encoding (must have the same length as the base)",
        },
    }

    tests = {"base": {"params": "", "roundtrip": False}}

    # Subclasses must define these
    alphabet: bytes = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"  # Default characters used for encoding (as bytes)
    bits_per_char: int = 6  # Number of bits each character represents
    padding: str = "="  # Padding character

    # Dictionary of alternative alphabets (can be overridden by subclasses)
    alphabets: Dict[str, bytes] = {}

    @classmethod
    def _get_alphabet(cls, alphabet_param: str = "") -> bytes:
        """Get the alphabet to use, either from parameter, named alphabet, or default"""
        if alphabet_param:
            # Check if it's a named alphabet
            if alphabet_param in cls.alphabets:
                return cls.alphabets[alphabet_param]
            # Otherwise treat it as a custom alphabet string
            try:
                alphabet_bytes = alphabet_param.encode("ascii")
            except UnicodeEncodeError as e:
                raise EncodeError(f"Alphabet must be ASCII: {e}") from e
            return alphabet_bytes

        return cls.alphabet

    @classmethod
    def _validate_alphabet(cls, alphabet: bytes):
        """Validate that the alphabet has the correct length"""
        expected_len = 1 << cls.bits_per_char
        if len(alphabet) != expected_len:
            raise EncodeError(
                f"{cls.__name__}: alphabet length ({len(alphabet)}) must equal 2^bits_per_char (2^{cls.bits_per_char}={expected_len})"
            )

    @classmethod
    def _validate_padding(cls, padding: str, alphabet: bytes) -> bytes:
        """Validate the padding character and return it as a byte"""
        try:
            padding_byte = padding.encode("ascii")
        except UnicodeEncodeError as e:
            raise DecodeError(f"padding ({padding}) must be ASCII") from e

        if len(padding_byte) != 1:
            raise DecodeError(f"padding ({padding}) must be a single character")

        if padding_byte in alphabet:
            raise DecodeError(f"padding ({padding}) can not be inside the alphabet")

        return padding_byte

    @classmethod
    def encode(
        cls, text: bytes, padding: str = "", no_padding: bool = False, alphabet: str = "", **kwargs
    ) -> bytes:
        """
        Encode bytes using power-of-two base encoding with bitwise operations

        Args:
            text: Input bytes to encode
            padding: Whether to include padding characters
            alphabet: Custom alphabet string or name of predefined alphabet

        Returns:
            Encoded bytes
        """
        # Get and validate the alphabet
        alphabet_bytes = cls._get_alphabet(alphabet)
        cls._validate_alphabet(alphabet_bytes)

        if not text:
            return b""

        result = bytearray()
        bit_buffer = 0
        bits_in_buffer = 0
        mask = (1 << cls.bits_per_char) - 1  # Mask to extract bits_per_char bits

        for byte in text:
            # Add byte to buffer
            bit_buffer = (bit_buffer << 8) | byte
            bits_in_buffer += 8

            # Extract as many complete chunks as possible
            while bits_in_buffer >= cls.bits_per_char:
                bits_in_buffer -= cls.bits_per_char
                index = (bit_buffer >> bits_in_buffer) & mask
                result.append(alphabet_bytes[index])

        # Handle remaining bits
        if bits_in_buffer > 0:
            # Shift remaining bits to align them to the left of the chunk
            index = (bit_buffer << (cls.bits_per_char - bits_in_buffer)) & mask
            result.append(alphabet_bytes[index])

        if not no_padding:
            # Add padding if requested
            padding = padding if padding else cls.padding
            padding_bytes = cls._validate_padding(padding, alphabet_bytes)

            # Calculate how many padding characters are needed
            # Padding ensures output length is a multiple of the encoding group size

            bits_per_byte = 8
            lcm = (cls.bits_per_char * bits_per_byte) // cls._gcd(cls.bits_per_char, bits_per_byte)
            chars_per_group = lcm // cls.bits_per_char

            padding_needed = (chars_per_group - (len(result) % chars_per_group)) % chars_per_group
            result.extend(padding_bytes * padding_needed)

        return bytes(result)

    @classmethod
    def decode(
        cls, text: bytes, padding: str = "", no_padding: bool = False, alphabet: str = "", **kwargs
    ) -> bytes:
        """
        Decode power-of-two base encoded bytes using bitwise operations

        Args:
            text: Encoded bytes to decode
            padding: Whether the input includes padding characters (ignored during decode)
            alphabet: Custom alphabet string or name of predefined alphabet

        Returns:
            Decoded bytes
        """
        # Get and validate the alphabet
        alphabet_bytes = cls._get_alphabet(alphabet)
        cls._validate_alphabet(alphabet_bytes)

        # Remove padding characters
        if not no_padding:
            padding = padding if padding else cls.padding
            padding_bytes = cls._validate_padding(padding, alphabet_bytes)
            text = text.rstrip(padding_bytes)

        if not text:
            return b""

        # Create reverse lookup table
        char_to_index = {alphabet_bytes[i]: i for i in range(len(alphabet_bytes))}

        result = bytearray()
        bit_buffer = 0
        bits_in_buffer = 0

        for byte in text:
            if byte not in char_to_index:
                raise DecodeError(
                    f"Invalid character '{chr(byte)}' (0x{byte:02x}) for {cls.__name__}"
                )

            index = char_to_index[byte]

            # Add bits to buffer
            bit_buffer = (bit_buffer << cls.bits_per_char) | index
            bits_in_buffer += cls.bits_per_char

            # Extract complete bytes
            while bits_in_buffer >= 8:
                bits_in_buffer -= 8
                byte_value = (bit_buffer >> bits_in_buffer) & 0xFF
                result.append(byte_value)

        # Note: Any remaining bits (less than 8) are padding bits and should be ignored

        return bytes(result)

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        """Calculate greatest common divisor"""
        while b:
            a, b = b, a % b
        return a
