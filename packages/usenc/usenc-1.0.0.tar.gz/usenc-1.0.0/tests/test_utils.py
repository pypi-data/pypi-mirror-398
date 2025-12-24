"""
Unit tests for utils.py helper functions
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from usenc.utils import escape_for_char_class, transform_keywords


class TestEscapeForCharClass:
    """Tests for the escape_for_char_class function."""

    def test_empty_string(self):
        """Test that empty strings are handled correctly."""
        assert escape_for_char_class("") == ""

    def test_regular_characters(self):
        """Test that regular characters pass through unchanged."""
        assert escape_for_char_class("abc123") == "abc123"
        assert escape_for_char_class("hello world") == "hello world"
        assert escape_for_char_class("ABC XYZ") == "ABC XYZ"

    def test_special_char_class_characters(self):
        """Test that special character class chars are escaped."""
        assert escape_for_char_class("-") == "\\-"
        assert escape_for_char_class("^") == "\\^"
        assert escape_for_char_class("]") == "\\]"
        assert escape_for_char_class("\\") == "\\\\"
        assert escape_for_char_class("a-z") == "a\\-z"
        assert escape_for_char_class("[^]") == "[\\^\\]"

    def test_hex_escape_sequences(self):
        """Test that hex escape sequences (\\xNN) are preserved."""
        assert escape_for_char_class("\\x41") == "\\x41"  # 'A'
        assert escape_for_char_class("\\x20") == "\\x20"  # space
        assert escape_for_char_class("\\xff") == "\\xff"
        assert escape_for_char_class("\\xAB") == "\\xAB"
        assert escape_for_char_class("\\x00") == "\\x00"
        assert escape_for_char_class("a\\x41b") == "a\\x41b"

    def test_invalid_hex_escapes(self):
        """Test that invalid hex escapes are handled correctly."""
        # Not enough hex digits
        assert escape_for_char_class("\\x4") == "\\x4"
        assert escape_for_char_class("\\xGG") == "\\xGG"
        # Backslash at end
        assert escape_for_char_class("\\") == "\\\\"

    def test_unicode_escape_sequences(self):
        """Test that unicode escape sequences (\\uNNNN) are preserved."""
        assert escape_for_char_class("\\u0041") == "\\u0041"  # 'A'
        assert escape_for_char_class("\\u00e9") == "\\u00e9"  # 'é'
        assert escape_for_char_class("\\uFFFF") == "\\uFFFF"
        assert escape_for_char_class("a\\u0041b") == "a\\u0041b"

    def test_long_unicode_escape_sequences(self):
        """Test that long unicode escape sequences (\\U00NNNNNN) are preserved."""
        assert escape_for_char_class("\\U00000041") == "\\U00000041"  # 'A'
        assert escape_for_char_class("\\U0001F600") == "\\U0001F600"  # emoji
        assert escape_for_char_class("\\U00010000") == "\\U00010000"
        assert escape_for_char_class("a\\U00000041b") == "a\\U00000041b"

    def test_octal_escape_sequences(self):
        """Test that octal escape sequences (\\NNN) are preserved."""
        assert escape_for_char_class("\\101") == "\\101"  # 'A'
        assert escape_for_char_class("\\377") == "\\377"  # max octal
        assert escape_for_char_class("\\0") == "\\0"
        assert escape_for_char_class("\\77") == "\\77"
        assert escape_for_char_class("a\\101b") == "a\\101b"

    def test_single_char_escapes(self):
        """Test that single-char escapes are preserved."""
        assert escape_for_char_class("\\n") == "\\n"
        assert escape_for_char_class("\\t") == "\\t"
        assert escape_for_char_class("\\r") == "\\r"
        assert escape_for_char_class("\\f") == "\\f"
        assert escape_for_char_class("\\v") == "\\v"
        assert escape_for_char_class("\\a") == "\\a"
        assert escape_for_char_class("\\b") == "\\b"
        assert escape_for_char_class("\\d") == "\\d"
        assert escape_for_char_class("\\D") == "\\D"
        assert escape_for_char_class("\\w") == "\\w"
        assert escape_for_char_class("\\W") == "\\W"
        assert escape_for_char_class("\\s") == "\\s"
        assert escape_for_char_class("\\S") == "\\S"

    def test_already_escaped_special_chars(self):
        """Test that already escaped special chars are preserved."""
        assert escape_for_char_class("\\-") == "\\-"
        assert escape_for_char_class("\\^") == "\\^"
        assert escape_for_char_class("\\]") == "\\]"
        assert escape_for_char_class("\\\\") == "\\\\"

    def test_mixed_content(self):
        """Test strings with mixed content types."""
        assert escape_for_char_class("abc\\x41def") == "abc\\x41def"
        assert escape_for_char_class("a-b\\nc") == "a\\-b\\nc"
        assert escape_for_char_class("test\\u0041-\\x42") == "test\\u0041\\-\\x42"
        assert escape_for_char_class("[a-z]\\n") == "[a\\-z\\]\\n"

    def test_backslash_at_end(self):
        """Test handling of backslash at the end of string."""
        assert escape_for_char_class("test\\") == "test\\\\"

    def test_multiple_special_chars(self):
        """Test multiple special chars in sequence."""
        assert escape_for_char_class("---") == "\\-\\-\\-"
        assert escape_for_char_class("^^^") == "\\^\\^\\^"
        assert escape_for_char_class("]]]") == "\\]\\]\\]"

    def test_edge_cases(self):
        """Test various edge cases."""
        # Single special char
        assert escape_for_char_class("-") == "\\-"
        # Only escape sequences
        assert escape_for_char_class("\\n\\t\\r") == "\\n\\t\\r"
        # Complex pattern
        assert escape_for_char_class("a-z0-9_\\-") == "a\\-z0\\-9_\\-"

    def test_non_special_backslash_escapes(self):
        """Test backslash followed by non-special characters."""
        # These should be preserved as-is
        assert escape_for_char_class("\\k") == "\\k"
        assert escape_for_char_class("\\z") == "\\z"
        assert escape_for_char_class("\\@") == "\\@"

    def test_incomplete_escapes_at_end(self):
        """Test incomplete escape sequences at end of string."""
        assert escape_for_char_class("test\\x") == "test\\x"
        assert escape_for_char_class("test\\u") == "test\\u"
        assert escape_for_char_class("test\\U") == "test\\U"

    def test_real_world_patterns(self):
        """Test realistic regex character class patterns."""
        # URL characters
        assert (
            escape_for_char_class("a-zA-Z0-9._~:/?#[]@!$&'()*+,;=")
            == "a\\-zA\\-Z0\\-9._~:/?#[\\]@!$&'()*+,;="
        )

        # Common punctuation
        assert escape_for_char_class(".,;:!?-") == ".,;:!?\\-"

        # Brackets and braces
        assert escape_for_char_class("[]{}()") == "[\\]{}()"


class TestTransformKeywords:
    """Tests for the transform_keywords function."""

    def test_empty_string(self):
        """Test that empty strings are handled correctly."""
        assert transform_keywords("") == ""

    def test_no_keywords(self):
        """Test strings without any keywords pass through unchanged."""
        assert transform_keywords("hello world") == "hello world"
        assert transform_keywords("abc123") == "abc123"
        assert transform_keywords("special!@#$%") == "special!@#$%"

    def test_all_keyword(self):
        """Test that 'all' keyword is transformed to \\s\\S."""
        assert transform_keywords("all") == "\\s\\S"

    def test_ascii_keyword(self):
        """Test that 'ascii' keyword is transformed to \\x00-\\x7f."""
        assert transform_keywords("ascii") == "\\x00-\\x7f"

    def test_utf8_keyword(self):
        """Test that 'utf8' keyword is transformed to \\u0080-\\U0010ffff."""
        assert transform_keywords("utf8") == "\\u0080-\\U0010ffff"

    def test_keywords_concatenated(self):
        """Test keywords directly concatenated without spaces."""
        assert transform_keywords("allasciiutf8") == "\\s\\S\\x00-\\x7f\\u0080-\\U0010ffff"
