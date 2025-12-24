import re

from ..utils import escape_for_char_class, transform_keywords
from .encoder import DecodeError, EncodeError, Encoder


class EscapeEncoder(Encoder):
    """
    Generic escape encoder.

    Encodes each character with the `cls.encode_char` function and add a prefix and a suffix.
    Characters to be encoded are selected by the `character_class` or `regex` parameter, and are
    fine tuned by the `include` and `exclude` parameters.

    The decoder uses `decode_class` to match sequences to be decoded by the `cls.decode_char` function
    """

    params = {
        "prefix": {"type": str, "default": "", "help": "Prefix string to each encoded character"},
        "suffix": {"type": str, "default": "", "help": "Suffix string to each encoded character"},
        "include": {
            "type": str,
            "default": "",
            "help": "Characters that should be encoded (can contain 'all', 'utf8' or 'ascii')",
        },
        "exclude": {"type": str, "default": "", "help": "Characters that should not be encoded"},
        "regex": {
            "type": str,
            "default": "",
            "help": "Regex override for characters that should be encoded",
        },
        "lowercase": {"action": "store_true", "help": "Use lowercase hex digits"},
    }

    tests = {
        "base": {"params": "", "roundtrip": False},
        "prefix": {"params": "--prefix pfx", "roundtrip": True},
        "suffix": {"params": "--suffix sfx", "roundtrip": True},
        "complex": {
            "params": "--prefix ${ --suffix } --lowercase --regex [^a-zA-Z]+",
            "roundtrip": True,
        },
        "include": {"params": "--include ghij", "roundtrip": True},
        "exclude": {"params": "--exclude abcd", "roundtrip": False},
        "include_all": {"params": "--include all", "roundtrip": True},
        "include_all_except_some": {"params": "--include all --exclude ghij", "roundtrip": False},
        "regex": {"params": "--regex [a-z]+", "roundtrip": False},
        "lowercase": {"params": "--lowercase", "roundtrip": False},
    }

    prefix: str = ""
    suffix: str = ""
    character_class: str = "\\s\\S"
    decode_class: str = "[a-fA-F0-9]{2}"

    @classmethod
    def encode_char(cls, c: str, **kwargs) -> str:
        raise NotImplementedError

    @classmethod
    def decode_char(cls, seq: str, **kwargs) -> str:
        raise NotImplementedError

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
        **kwargs,
    ) -> bytes:
        if regex == "":
            # Convert include and exlude strings as regex character classes
            # Build a regex that matches characters to be encoded
            safe_include = transform_keywords(escape_for_char_class(include))
            safe_exclude = transform_keywords(escape_for_char_class(exclude))

            regex = rf"[{cls.character_class}]"
            if safe_include != "":
                regex = rf"({regex}|[{safe_include}])"
            if safe_exclude != "":
                regex = rf"(?![{safe_exclude}]){regex}"
            regex = rf"(?:{regex})+"

        try:
            # Use a custom provided regex
            enc_regex = re.compile(regex)
        except re.error as e:
            raise EncodeError(f"regex error: {e}") from e

        prefix = cls.prefix if prefix == "" else prefix
        suffix = cls.suffix if suffix == "" else suffix

        def replace(match):
            # Encode this part of the string
            enc_string = ""
            for x in match.group(0):
                enc_string += cls.encode_char(
                    x,
                    lowercase=lowercase,
                    prefix=prefix,
                    suffix=suffix,
                    input_charset=input_charset,
                    output_charset=output_charset,
                    **kwargs,
                )
            return enc_string

        try:
            return enc_regex.sub(replace, text.decode(input_charset)).encode(output_charset)
        except UnicodeDecodeError as e:
            raise EncodeError(f"input-charset '{input_charset}' decoding failed: {e}") from e
        except UnicodeEncodeError as e:
            raise EncodeError(f"output-charset '{output_charset}' encoding failed: {e}") from e

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
        **kwargs,
    ) -> bytes:
        prefix = cls.prefix if prefix == "" else prefix
        suffix = cls.suffix if suffix == "" else suffix

        def replace(match):
            # Decode a sequence of chars
            return cls.decode_char(
                match.group(0),
                prefix=prefix,
                suffix=suffix,
                input_charset=input_charset,
                output_charset=output_charset,
                **kwargs,
            )

        try:
            return re.sub(
                f"({re.escape(prefix)}({cls.decode_class}){re.escape(suffix)})+",
                replace,
                text.decode(input_charset),
            ).encode(output_charset)
        except UnicodeDecodeError as e:
            raise DecodeError(f"input-charset '{input_charset}' decoding failed: {e}") from e
        except UnicodeEncodeError as e:
            raise DecodeError(f"output-charset '{output_charset}' encoding failed: {e}") from e
