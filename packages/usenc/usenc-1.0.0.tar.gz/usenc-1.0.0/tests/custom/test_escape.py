import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from usenc.encoders.encoder import EncodeError
from usenc.encoders.escape import EscapeEncoder


def test_invalid_regex():
    with pytest.raises(EncodeError, match="regex error: unterminated character set at position 0"):
        EscapeEncoder.encode(b"hello world", regex="[a-z")


def test_unimplemented_encode():
    with pytest.raises(NotImplementedError):
        EscapeEncoder.encode(b"hello world")


def test_unimplemented_decode():
    with pytest.raises(NotImplementedError):
        EscapeEncoder.decode(b"68656C6C6F20776F726C64")
