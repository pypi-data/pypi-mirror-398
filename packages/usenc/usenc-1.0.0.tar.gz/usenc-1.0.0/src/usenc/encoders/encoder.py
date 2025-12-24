from typing import Any, Dict, TypedDict


class EncodeError(Exception):
    """Exception raised when encoding fails."""

    pass


class DecodeError(Exception):
    """Exception raised when decoding fails."""

    pass


class Encoder:
    """Base class for encoders - makes adding new encoders simple"""

    class Args(TypedDict, total=False):
        type: Any
        default: Any
        help: str
        action: str
        nargs: str
        const: str
        required: bool

    class ConfigTests(TypedDict):
        params: str
        roundtrip: bool

    params: Dict[str, Args] = {}
    tests: Dict[str, ConfigTests] = {"base": {"params": "", "roundtrip": False}}

    @classmethod
    def encode(cls, text: bytes, **kwargs) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, text: bytes, **kwargs) -> bytes:
        raise NotImplementedError
