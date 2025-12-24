import re


def escape_for_char_class(s):
    """
    Escape a string so it can safely be used inside a regex character class.
    Allows all standard regex character escapes (\\xNN, \\uNNNN, \\U00NNNNNN, \\NNN).
    Denies characters that have a meaning in a character class (-, ^, ], \\).
    """
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            next_char = s[i + 1]

            # \xNN - hex escape
            if (
                next_char == "x"
                and i + 3 < len(s)
                and re.match(r"[0-9a-fA-F]{2}", s[i + 2 : i + 4])
            ):
                result.append(s[i : i + 4])
                i += 4
            # \uNNNN - unicode escape
            elif (
                next_char == "u"
                and i + 5 < len(s)
                and re.match(r"[0-9a-fA-F]{4}", s[i + 2 : i + 6])
            ):
                result.append(s[i : i + 6])
                i += 6
            # \U00NNNNNN - long unicode escape
            elif (
                next_char == "U"
                and i + 9 < len(s)
                and re.match(r"[0-9a-fA-F]{8}", s[i + 2 : i + 10])
            ):
                result.append(s[i : i + 10])
                i += 10
            # \NNN - octal escape (1-3 digits)
            elif next_char in "01234567":
                match = re.match(r"\\[0-7]{1,3}", s[i:])
                if match:
                    result.append(match.group())
                    i += len(match.group())
            # Single-char escapes: \n, \t, \r, \d, \w, \s, etc.
            elif next_char in "nrtfvabdDwWsS":
                result.append(s[i : i + 2])
                i += 2
            # Escaped special char (user already escaped it)
            else:
                result.append(s[i : i + 2])
                i += 2
        elif s[i] in r"\]^-":
            result.append("\\" + s[i])
            i += 1
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


def transform_keywords(s):
    """
    Convert keywords ('all', 'ascii', 'utf8') to character classes for use in regexes
    """
    s = s.replace("all", "\\s\\S")  # match both whitespace and non-whitespace => everything
    s = s.replace("ascii", "\\x00-\\x7f")
    s = s.replace("utf8", "\\u0080-\\U0010ffff")
    return s
