from typing import Tuple

from .escape import EscapeEncoder


class UnicodeEncoder(EscapeEncoder):
    """
    Unicode escapes encoding

    Encodes each character with its unicode representation and an optional prefix/suffix.

    Examples:
    hello world -> \\u0068\\u0065\\u006C\\u006C\\u006F\\u0020\\u0077\\u006F\\u0072\\u006C\\u0064
    café -> \\u0063\\u0061\\u0066\\u00E9
    日本語 -> \\u65E5\\u672C\\u8A9E
    🚀 -> \\u1F680
    """

    prefix = "\\u"
    suffix = ""
    decode_class: str = "[a-fA-F0-9]{2,8}"

    params = {
        **EscapeEncoder.params,
        "var_length": {"action": "store_true", "help": "Use variable length encoding"},
        "long": {"action": "store_true", "help": "Use 8 hex digits instead of 4"},
    }

    tests = {
        **EscapeEncoder.tests,
        "var_length": {"params": "--var-length", "roundtrip": True},
        "long": {"params": "--long", "roundtrip": True},
    }

    @classmethod
    def encode_char(
        cls,
        c: str,
        lowercase: bool = False,
        prefix: str = "",
        suffix: str = "",
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        var_length: bool = False,
        long: bool = False,
        **kwargs,
    ) -> str:
        if var_length:
            hex_format = "{:x}" if lowercase else "{:X}"
        else:
            if long:
                hex_format = "{:08x}" if lowercase else "{:08X}"
            else:
                hex_format = "{:04x}" if lowercase else "{:04X}"

        return prefix + hex_format.format(ord(c)) + suffix

    @classmethod
    def decode_char(
        cls,
        seq: str,
        prefix: str = "",
        suffix: str = "",
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        var_length: bool = False,
        long: bool = False,
        **kwargs,
    ) -> str:
        plen = len(prefix)
        slen = len(suffix)

        decode_arr = []

        i = 0
        while i < len(seq):
            i += plen

            char = ""

            if suffix != "":
                while seq[i] != suffix[0]:
                    char += seq[i]
                    i += 1
                i += slen
            else:
                while i < len(seq) and seq[i] != prefix[0]:
                    char += seq[i]
                    i += 1

            decode_arr.append(chr(int(char, 16)))

        return "".join(decode_arr)

    @classmethod
    def _compute_affix(
        cls, prefix: str = "", suffix: str = "", var_length: bool = False, long: bool = False
    ) -> Tuple[str, str]:
        if prefix != "":
            computed_prefix = prefix
        elif var_length:
            computed_prefix = "\\u{"
        elif long:
            computed_prefix = "\\U"
        else:
            computed_prefix = cls.prefix

        if suffix != "":
            computed_suffix = suffix
        elif var_length:
            computed_suffix = "}"
        else:
            computed_suffix = cls.suffix

        return computed_prefix, computed_suffix

    @classmethod
    def encode(
        cls,
        text: bytes,
        prefix: str = "",
        suffix: str = "",
        include: str = "",
        exclude: str = "",
        regex: str = "",
        lowercase: bool = False,
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        var_length: bool = False,
        long: bool = False,
        **kwargs,
    ) -> bytes:
        computed_prefix, computed_suffix = cls._compute_affix(
            prefix=prefix, suffix=suffix, var_length=var_length, long=long
        )
        return super().encode(
            text,
            prefix=computed_prefix,
            suffix=computed_suffix,
            include=include,
            exclude=exclude,
            regex=regex,
            lowercase=lowercase,
            input_charset=input_charset,
            output_charset=output_charset,
            var_length=var_length,
            long=long,
            **kwargs,
        )

    @classmethod
    def decode(
        cls,
        text: bytes,
        prefix: str = "",
        suffix: str = "",
        include: str = "",
        exclude: str = "",
        regex: str = "",
        lowercase: bool = False,
        input_charset: str = "utf8",
        output_charset: str = "utf8",
        var_length: bool = False,
        long: bool = False,
        **kwargs,
    ) -> bytes:
        computed_prefix, computed_suffix = cls._compute_affix(
            prefix=prefix, suffix=suffix, var_length=var_length, long=long
        )
        return super().decode(
            text,
            prefix=computed_prefix,
            suffix=computed_suffix,
            include=include,
            exclude=exclude,
            regex=regex,
            lowercase=lowercase,
            input_charset=input_charset,
            output_charset=output_charset,
            var_length=var_length,
            long=long,
            **kwargs,
        )
