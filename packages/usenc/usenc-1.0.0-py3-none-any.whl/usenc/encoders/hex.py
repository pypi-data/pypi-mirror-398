from .escape import EscapeEncoder


class HexEncoder(EscapeEncoder):
    """
    Hexadecimal string encoding

    Encodes each character with its hex 2-digits representation and an optional prefix/suffix

    Examples:
    hello world -> 68656C6C6F20776F726C64
    escape "me" -> 65736361706520226D6522
    café -> 636166C3A9
    http://example.org -> 687474703A2F2F6578616D706C652E6F7267
    """

    character_class: str = "\\s\\S"
    decode_class: str = "[a-fA-F0-9]{2}"

    @classmethod
    def encode_char(
        cls,
        c: str,
        lowercase: bool = False,
        prefix: str = "",
        suffix: str = "",
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        **kwargs,
    ) -> str:
        hex_format = "{:02x}" if lowercase else "{:02X}"
        return "".join([prefix + hex_format.format(b) + suffix for b in c.encode(output_charset)])

    @classmethod
    def decode_char(
        cls,
        seq: str,
        prefix: str = "",
        suffix: str = "",
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        **kwargs,
    ) -> str:
        plen = len(prefix)
        slen = len(suffix)
        hex_str = "".join([seq[i : i + 2] for i in range(plen, len(seq), slen + 2 + plen)])
        return bytes.fromhex(hex_str).decode(input_charset)
