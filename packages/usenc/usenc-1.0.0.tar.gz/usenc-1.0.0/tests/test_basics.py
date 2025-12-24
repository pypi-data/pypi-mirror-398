"""
Simple checks that test if the encoder is setup properly
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from usenc.encoders import ENCODERS


class TestEncoderBasics:
    """Basic sanity tests for all encoders."""

    @pytest.mark.parametrize("encoder_name", sorted(ENCODERS.keys()))
    def test_encoder_exists(self, encoder_name: str):
        """Verify each encoder is properly registered."""
        assert encoder_name in ENCODERS
        assert ENCODERS[encoder_name] is not None

    @pytest.mark.parametrize("encoder_name", sorted(ENCODERS.keys()))
    def test_encoder_has_encode_method(self, encoder_name: str):
        """Verify each encoder has an encode method."""
        encoder_class = ENCODERS[encoder_name]
        assert hasattr(encoder_class, "encode")
        assert callable(encoder_class.encode)
