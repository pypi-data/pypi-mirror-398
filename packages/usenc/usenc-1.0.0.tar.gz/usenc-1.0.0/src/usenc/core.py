from .encoders import ENCODERS


class EncoderNotFoundError(Exception):
    """Exception raised when an encoder is not found."""

    pass


def encode(text: bytes, encoder_name: str, **encoder_params) -> bytes:
    """Encode a single text string"""
    encoder = ENCODERS.get(encoder_name)
    if not encoder:
        raise EncoderNotFoundError(f"Unknown encoder: {encoder_name}")

    return encoder.encode(text, **encoder_params)


def decode(text: bytes, encoder_name: str, **encoder_params) -> bytes:
    """Decode a single text string"""
    encoder = ENCODERS.get(encoder_name)
    if not encoder:
        raise EncoderNotFoundError(f"Unknown encoder: {encoder_name}")

    return encoder.decode(text, **encoder_params)
