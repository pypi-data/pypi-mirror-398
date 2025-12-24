from .url import UrlEncoder


class DoubleUrlEncoder(UrlEncoder):
    """
    Double URL encoding (RFC 3986 percent encoding)

    Apply the URL Encoder twice on the input string.

    It is the same as doing `echo hello | usenc url | usenc url`

    Examples:
    hello world -> hello%2520world
    http://example.org -> http%253A%252F%252Fexample.org
    index.php?key=value&other=1 -> index.php%253Fkey%253Dvalue%2526other%253D1
    <div>hello</div> -> %253Cdiv%253Ehello%253C%252Fdiv%253E
    """

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
        return super().encode(
            super().encode(
                text,
                prefix=prefix,
                suffix=suffix,
                include=include,
                exclude=exclude,
                regex=regex,
                lowercase=lowercase,
                input_charset=input_charset,
                output_charset=output_charset,
                **kwargs,
            ),
            prefix=prefix,
            suffix=suffix,
            include=include,
            exclude=exclude,
            regex=regex,
            lowercase=lowercase,
            input_charset=input_charset,
            output_charset=output_charset,
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
        **kwargs,
    ) -> bytes:
        return super().decode(
            super().decode(
                text,
                prefix=prefix,
                suffix=suffix,
                include=include,
                exclude=exclude,
                regex=regex,
                lowercase=lowercase,
                input_charset=input_charset,
                output_charset=output_charset,
                **kwargs,
            ),
            prefix=prefix,
            suffix=suffix,
            include=include,
            exclude=exclude,
            regex=regex,
            lowercase=lowercase,
            input_charset=input_charset,
            output_charset=output_charset,
            **kwargs,
        )
