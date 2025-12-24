from .base2n import Base2NEncoder


class Base64Encoder(Base2NEncoder):
    """
    Standard Base64 encoding (RFC 4648)

    Encodes binary data using 64 ASCII characters (A-Z, a-z, 0-9, +, /)
    Each character represents 6 bits of data.

    Alternative alphabets:

        - standard: A-Z, a-z, 0-9, +, / (default)
        - url: A-Z, a-z, 0-9, -, _ (URL-safe variant)

    Examples:
        hello -> aGVsbG8=
        hello world -> aGVsbG8gd29ybGQ=
    """

    alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    bits_per_char = 6

    alphabets = {
        "standard": b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
        "url": b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",
    }

    tests = {
        "base": {"params": "", "roundtrip": True},
        "padding": {"params": "--padding *", "roundtrip": True},
        "no_padding": {"params": "--no-padding", "roundtrip": True},
        "url_alphabet": {"params": "--alphabet url", "roundtrip": True},
    }
