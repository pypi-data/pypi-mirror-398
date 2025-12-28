"""
Encoding detection and text processing utilities.

This module provides functionality for:
- Detecting character encoding from binary data
- Decoding binary data to text
- Normalizing newlines and text formatting
- Checking if data is binary or text

Note:
    The charset_normalizer library may misidentify Japanese encodings
    (shift_jis as cp932, euc-jp as big5). For more accurate Japanese
    encoding detection, enable nkf usage in settings.
"""

import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._helpers.decode_binary_to_text import decode_binary_to_text
    from ._helpers.detect_encoding import detect_encoding
    from ._helpers.get_default_encoding import get_default_encoding
    from ._helpers.is_binary import is_binary
    from ._utils.normalize_newlines import normalize_newlines
    from .settings import settings_manager

__version__ = "1.0.0"

__all__ = [
    # .helpers
    "decode_binary_to_text",
    "detect_encoding",
    "get_default_encoding",
    "is_binary",
    # .settings
    "settings_manager",
    # .utils
    "normalize_newlines",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # .helpers
        "decode_binary_to_text": "._helpers.decode_binary_to_text",
        "detect_encoding": "._helpers.detect_encoding",
        "get_default_encoding": "._helpers.get_default_encoding",
        "is_binary": "._helpers.is_binary",
        # .settings
        "settings_manager": ".settings",
        # .utils
        "normalize_newlines": "._utils.normalize_newlines",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
