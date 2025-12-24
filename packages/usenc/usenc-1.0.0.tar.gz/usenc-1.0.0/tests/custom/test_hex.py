import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from usenc.encoders.encoder import DecodeError, EncodeError
from usenc.encoders.hex import HexEncoder


def test_encode_invalid_character():
    with pytest.raises(EncodeError, match="input-charset 'utf8' decoding failed"):
        HexEncoder.encode(b"h\xe9llo")

    with pytest.raises(EncodeError, match="output-charset 'ascii' encoding failed"):
        HexEncoder.encode(b"h\xc3\xa9llo", output_charset="ascii")


def test_decode_invalid_character():
    with pytest.raises(DecodeError, match="input-charset 'utf8' decoding failed"):
        HexEncoder.decode(b"hE9llo")

    with pytest.raises(DecodeError, match="output-charset 'ascii' encoding failed"):
        HexEncoder.decode(b"h\xc3\xa9llo", output_charset="ascii")
