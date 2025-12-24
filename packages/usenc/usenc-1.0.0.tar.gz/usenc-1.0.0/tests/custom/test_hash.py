import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from usenc.encoders.encoder import DecodeError, EncodeError
from usenc.encoders.hash import HashEncoder


def test_hash_no_name():
    """Test error when algorithm is not provided and not defined in class"""
    with pytest.raises(EncodeError, match="algorithm parameter is required"):
        HashEncoder.encode(b"test")


def test_hash_invalid_algorithm():
    """Test error with invalid hash algorithm name"""
    with pytest.raises(EncodeError, match="Unknown hash algorithm"):
        HashEncoder.encode(b"test", algorithm="invalid_hash_algorithm")


def test_hash_cannot_decode():
    """Test that hash encoders cannot decode"""
    with pytest.raises(DecodeError, match="hash functions cannot be decoded"):
        HashEncoder.decode(b"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
