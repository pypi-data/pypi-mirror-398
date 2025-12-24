import argparse

from usenc import cli
from usenc.encoders import ENCODERS


def load_samples_file(path):
    """Load test samples, filtering out comments and empty lines."""
    samples = []

    with open(path, "rb") as f:
        for line in f:
            # Strip trailing newline but preserve the content
            line = line.rstrip(b"\n")
            # Skip comment lines (starting with #)
            if line.startswith(b"#"):
                continue
            # Include all lines, even empty ones (they're valid test cases)
            samples.append(line)

    return samples


def load_encoders_tests(only_roundtrip: bool):
    test_parameters = []
    for encoder_name, encoder in ENCODERS.items():
        for test_name, test_params in encoder.tests.items():
            if only_roundtrip and not test_params["roundtrip"]:
                continue
            test_parameters.append((encoder_name, test_name, test_params["params"]))
    return test_parameters


def parse_encoder_params(encoder_name, params):
    parser = argparse.ArgumentParser()
    cli.add_encoder_params(parser, encoder_name)
    args = parser.parse_args(params.split())
    return vars(args)
