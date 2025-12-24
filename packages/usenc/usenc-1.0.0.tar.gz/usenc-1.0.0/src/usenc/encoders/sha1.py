from .hash import HashEncoder


class Sha1Encoder(HashEncoder):
    """
    SHA-1 hash encoding

    Computes SHA-1 hash of input bytes and outputs the hex digest.
    SHA-1 is a one-way hash function and cannot be decoded.

    Note: SHA-1 is cryptographically broken and should not be used for security purposes.

    Examples:
    hello world -> 2AAE6C35C94FCFB415DBE95F408B9CE91EE846ED
    """

    algorithm = "sha1"

    # Exclude algorithm parameter since it's defined as a class attribute
    params = {k: v for k, v in HashEncoder.params.items() if k not in {"algorithm"}}

    tests = {
        "base": {"params": "", "roundtrip": False},
        "lowercase": {"params": "--lowercase", "roundtrip": False},
    }
