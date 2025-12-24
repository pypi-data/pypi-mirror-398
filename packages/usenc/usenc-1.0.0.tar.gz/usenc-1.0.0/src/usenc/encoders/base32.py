from .base2n import Base2NEncoder


class Base32Encoder(Base2NEncoder):
    """
    Standard Base32 encoding (RFC 4648)

    Encodes binary data using 32 ASCII characters (A-Z, 2-7)
    Each character represents 5 bits of data.

    Alternative alphabets:

        - standard: A-Z, 2-7 (default, RFC 4648)
        - hex: 0-9, A-V (Base32hex, RFC 4648)
        - crockford: 0-9, A-Z excluding I, L, O, U (Crockford Base32)
        - z: ybndrfg8ejkmcpqxot1uwisza345h769 (z-base-32, human-oriented)

    Examples:
        hello -> NBSWY3DP
        hello world -> NBSWY3DPEB3W64TMMQ======
    """

    alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    bits_per_char = 5

    alphabets = {
        "standard": b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
        "hex": b"0123456789ABCDEFGHIJKLMNOPQRSTUV",
        "crockford": b"0123456789ABCDEFGHJKMNPQRSTVWXYZ",
        "z": b"ybndrfg8ejkmcpqxot1uwisza345h769",
    }

    tests = {
        "base": {"params": "", "roundtrip": True},
        "padding": {"params": "--padding *", "roundtrip": True},
        "no_padding": {"params": "--no-padding", "roundtrip": True},
        "hex_alphabet": {"params": "--alphabet hex", "roundtrip": True},
        "crockford_alphabet": {"params": "--alphabet crockford", "roundtrip": True},
        "z_alphabet": {"params": "--alphabet z", "roundtrip": True},
    }
