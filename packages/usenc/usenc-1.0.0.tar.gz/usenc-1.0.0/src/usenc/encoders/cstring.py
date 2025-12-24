from .hex import HexEncoder


class CStringEncoder(HexEncoder):
    """
    C string escaping

    Encodes special characters and utf8 characters with a \\x prefixed hex value.

    Examples:
    hello world -> hello\\x20world
    escape "me" -> escape\\x20\\x22me\\x22
    café -> caf\\xC3\\xA9
    http://example.org -> http\\x3A\\x2F\\x2Fexample.org
    """

    character_class: str = "^A-Za-z0-9\\-_.!~*'()"
    prefix = "\\x"

    # Exclude parameters since they're defined as a class attribute
    params = {k: v for k, v in HexEncoder.params.items() if k not in {"prefix", "suffix"}}
    tests = {k: v for k, v in HexEncoder.tests.items() if k not in {"prefix", "suffix", "complex"}}
