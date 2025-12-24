import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from usenc.encoders.base2n import Base2NEncoder
from usenc.encoders.encoder import DecodeError, EncodeError


class TestEncoder(Base2NEncoder):
    """Test encoder for Base2N validation tests"""

    alphabet = b"0123456789ABCDEF"
    bits_per_char = 4


def test_non_ascii_alphabet():
    with pytest.raises(EncodeError, match=r"Alphabet must be ASCII"):
        TestEncoder.encode(b"test", alphabet="0123456789ABCDE\u00e9")


def test_wrong_alphabet_length():
    with pytest.raises(EncodeError, match=r"alphabet length .* must equal 2\^bits_per_char"):
        TestEncoder.encode(b"test", alphabet="0123456789ABC")


def test_non_ascii_padding():
    with pytest.raises(DecodeError, match=r"padding \(é\) must be ASCII"):
        TestEncoder.encode(b"test", padding="é")


def test_padding_in_alphabet():
    with pytest.raises(DecodeError, match=r"padding \(A\) can not be inside the alphabet"):
        TestEncoder.encode(b"test", padding="A")


def test_padding_too_long():
    with pytest.raises(DecodeError, match=r"padding \(==\) must be a single character"):
        TestEncoder.encode(b"test", padding="==")


def test_invalid_decode_character():
    with pytest.raises(DecodeError, match=r"Invalid character"):
        TestEncoder.decode(b"68656C6C6Z")
