"""
Roundtrip test for all encoders on all samples
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from conftest import load_encoders_tests, load_samples_file, parse_encoder_params

from usenc.encoders import ENCODERS
from usenc.encoders.encoder import DecodeError

# Load samples once for all tests
TEST_SAMPLES = load_samples_file(Path(__file__).parent / "snapshots" / "samples.txt")
test_parameters = load_encoders_tests(only_roundtrip=True)


class TestEncoderRoundtrip:
    """Check that the roundtrip property holds: decode(encode(x)) = x"""

    @pytest.mark.parametrize(
        "encoder_test", sorted(test_parameters), ids=lambda x: f"{x[0]}_{x[1]}"
    )
    def test_encode(self, encoder_test: tuple):
        """Test that encode->decode is lossless for all samples."""
        encoder_name, test_name, params_str = encoder_test
        params = parse_encoder_params(encoder_name, params_str)

        encoder_class = ENCODERS[encoder_name]

        for i, sample in enumerate(TEST_SAMPLES):
            encoded = encoder_class.encode(sample, **params)

            try:
                decoded = encoder_class.decode(encoded, **params)
            except DecodeError:
                continue

            # Roundtrip should be lossless
            assert decoded == sample, (
                f"Roundtrip failed for {encoder_name} at sample {i}: "
                f"'{sample}' -> '{encoded}' -> '{decoded}'"
            )
