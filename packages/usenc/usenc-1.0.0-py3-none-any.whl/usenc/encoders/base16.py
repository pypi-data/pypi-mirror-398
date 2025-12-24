from .base2n import Base2NEncoder


class Base16Encoder(Base2NEncoder):
    """
    Standard Base16 encoding (RFC 4648)

    Encodes binary data using 16 ASCII characters (0-9, A-F)
    Each character represents 4 bits of data.

    Alternative alphabets:

        - upper: 0-9, A-F (default, uppercase)
        - lower: 0-9, a-f (lowercase)

    Examples:
        hello -> 68656C6C6F
        hello world -> 68656C6C6F20776F726C64
    """

    alphabet = b"0123456789ABCDEF"
    bits_per_char = 4

    alphabets = {"upper": b"0123456789ABCDEF", "lower": b"0123456789abcdef"}

    tests = {
        "base": {"params": "", "roundtrip": True},
        "padding": {"params": "--padding =", "roundtrip": True},
        "lower_alphabet": {"params": "--alphabet lower", "roundtrip": True},
    }
