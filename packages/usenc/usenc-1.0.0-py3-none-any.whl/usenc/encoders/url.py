from .hex import HexEncoder


class UrlEncoder(HexEncoder):
    """
    Standard URL encoding (RFC 3986 percent encoding)

    Encodes special characters and utf8 characters with a percent
    prefixed hex value. Produces the same encoding as
    javascript `encodeURIComponent` by default.

    Examples:
    hello world -> hello%20world
    http://example.org -> http%3A%2F%2Fexample.org
    index.php?key=value&other=1 -> index.php%3Fkey%3Dvalue%26other%3D1
    <div>hello</div> -> %3Cdiv%3Ehello%3C%2Fdiv%3E
    """

    character_class: str = "^A-Za-z0-9\\-_.!~*'()"
    prefix = "%"

    # Exclude prefix parameter since it's defined as a class attribute
    params = {k: v for k, v in HexEncoder.params.items() if k not in {"prefix", "suffix"}}

    tests = {"base": {"params": "", "roundtrip": True}}
