from .hash import HashEncoder


class Sha256Encoder(HashEncoder):
    """
    SHA-256 hash encoding

    Computes SHA-256 hash of input bytes and outputs the hex digest.
    SHA-256 is a one-way hash function and cannot be decoded.

    SHA-256 is part of the SHA-2 family and is currently considered secure
    for cryptographic purposes.

    Examples:
    hello world -> B94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9
    """

    algorithm = "sha256"

    # Exclude algorithm parameter since it's defined as a class attribute
    params = {k: v for k, v in HashEncoder.params.items() if k not in {"algorithm"}}

    tests = {
        "base": {"params": "", "roundtrip": False},
        "lowercase": {"params": "--lowercase", "roundtrip": False},
    }
