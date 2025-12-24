"""
Comprehensive encoder tests using snapshot testing.

This module tests all encoders against test_samples.txt and compares
the results against stored snapshots to detect any regression in encoding behavior.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from conftest import load_encoders_tests, load_samples_file, parse_encoder_params

from usenc.encoders import ENCODERS

# Load samples once for all tests
TEST_SAMPLES = load_samples_file(Path(__file__).parent / "snapshots" / "samples.txt")

# Load parameters tests
test_parameters = load_encoders_tests(only_roundtrip=False)


class TestEncoderSnapshots:
    """Test all encoders against snapshots for regression detection."""

    @pytest.mark.parametrize(
        "encoder_test", sorted(test_parameters), ids=lambda x: f"{x[0]}_{x[1]}"
    )
    def test_encode(self, encoder_test: tuple):
        """Test encoding of each sample for each encoder against snapshot."""
        encoder_name, test_name, params_str = encoder_test
        params = parse_encoder_params(encoder_name, params_str)

        encoder_class = ENCODERS[encoder_name]
        encoded_samples = []

        for sample in TEST_SAMPLES:
            encoded_samples.append(encoder_class.encode(sample, **params))

        # Path to snapshot file
        snapshot_dir = Path(__file__).parent / "snapshots" / encoder_name
        snapshot_file = snapshot_dir / f"{test_name}.txt"

        # Create snapshot if it doesn't exist
        if not snapshot_file.exists():
            snapshot_dir.mkdir(exist_ok=True)
            with open(snapshot_file, "wb") as f:
                for encoded in encoded_samples:
                    f.write(encoded + b"\n")
            pytest.skip(f"Generated new snapshot for {encoder_name}")

        # Load expected snapshot
        expected_samples = load_samples_file(snapshot_file)

        # Assert against snapshot
        assert encoded_samples == expected_samples
