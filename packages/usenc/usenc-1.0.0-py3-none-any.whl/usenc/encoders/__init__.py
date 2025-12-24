import importlib
import inspect
from pathlib import Path
from typing import Dict, Type

from .encoder import Encoder


def discover_encoders() -> Dict[str, Type[Encoder]]:
    """
    Automatically discover and register all encoder classes in this package
    """
    encoders = {}
    encoders_dir = Path(__file__).parent

    # Find all Python files except __init__.py and base.py
    for filepath in encoders_dir.glob("*.py"):
        if filepath.name in ("__init__.py"):
            continue

        # Import the module
        module_name = filepath.stem
        module = importlib.import_module(f".{module_name}", package=__package__)

        # Find all Encoder subclasses in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Encoder) and obj is not Encoder:
                if name in ("Encoder", "TestEncoder", "EscapeEncoder", "Base2NEncoder"):
                    continue
                # Generate encoder key from class name (UrlEncoder -> url)
                encoder_key = name.replace("Encoder", "").lower()
                encoders[encoder_key] = obj

    return encoders


ENCODERS = discover_encoders()
__all__ = ["Encoder", "ENCODERS"]
