import re
from html.entities import codepoint2name, name2codepoint

from .escape import EscapeEncoder


class HtmlEncoder(EscapeEncoder):
    """
    HTML Entities encoding

    Encodes each character with its html escaped entity, based on the WHATWG HTML Living Standard.
    The full list of named character is available at https://html.spec.whatwg.org/multipage/named-characters.html

    This encoder uses Python's html.entities module for the named characters, and encodes the
    others with their decimal or hexadecimal representation.

    Examples:
    hello world -> hello world
    <p>hello</p> -> &#lt;p&#gt;hello&#lt;/p&#gt;
    <a href="/hello">hello</a> -> &#lt;a href=&#quot;/hello&#quot;&#gt;hello&#lt;/a&#gt;
    café -> caf&#eacute;
    """

    params = {
        **{k: v for k, v in EscapeEncoder.params.items() if k not in {"prefix", "suffix"}},
        "hex": {"action": "store_true", "help": "Use hexadecimal instead of decimal"},
    }

    tests = {
        **{
            k: v for k, v in EscapeEncoder.tests.items() if k not in {"prefix", "suffix", "complex"}
        },
        "hex": {"params": "--hex", "roundtrip": True},
    }

    prefix = "&#"
    suffix = ";"
    character_class: str = "<>&\"'\x80-\U0010ffff"
    decode_class: str = "[^&#;]+"

    @classmethod
    def encode_char(
        cls,
        c: str,
        lowercase: bool = False,
        prefix: str = "",
        suffix: str = "",
        hex: bool = False,
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        **kwargs,
    ) -> str:
        codepoint = ord(c)
        try:
            return prefix + codepoint2name[codepoint] + suffix
        except KeyError:
            return prefix + (f"{codepoint:x}" if hex else f"{codepoint}") + suffix

    @classmethod
    def decode_char(
        cls,
        seq: str,
        prefix: str = "",
        suffix: str = "",
        hex: bool = False,
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        **kwargs,
    ) -> str:
        def replace(match):
            try:
                return chr(name2codepoint[match.group(1)])
            except KeyError:
                if hex:
                    return chr(int(match.group(1), 16))
                else:
                    return chr(int(match.group(1)))

        hex_str = re.sub(f"{prefix}(.+?){suffix}", replace, seq)
        return hex_str
