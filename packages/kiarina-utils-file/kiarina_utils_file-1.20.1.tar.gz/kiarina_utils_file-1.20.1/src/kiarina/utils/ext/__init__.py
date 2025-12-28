"""
File extension detection and processing utilities.

This module provides functionality for:
- Detecting file extensions from MIME types
- Extracting file extensions from file paths or URLs
- Handling multi-part extensions (e.g., .tar.gz, .tar.gz.gpg)
- Converting between MIME types and file extensions

Examples:
    >>> import kiarina.utils.ext as ke
    >>>
    >>> # Detect extension from MIME type
    >>> extension = ke.detect_extension("application/json")
    >>>
    >>> # Extract extension from file path
    >>> extension = ke.extract_extension("document.tar.gz")
    >>>
    >>> # Extract extension from URL
    >>> extension = ke.extract_extension("https://example.com/file.tar.gz?param=value")

Note:
    This module supports multi-part extensions and can handle complex file
    naming patterns including archive, compression, and encryption extensions.
"""

# pip install kiarina-utils-ext
import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._helpers.detect_extension import detect_extension
    from ._helpers.extract_extension import extract_extension
    from .settings import settings_manager

__version__ = "1.0.0"

__all__ = [
    # .helpers
    "detect_extension",
    "extract_extension",
    # .settings
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # .helpers
        "detect_extension": "._helpers.detect_extension",
        "extract_extension": "._helpers.extract_extension",
        # .settings
        "settings_manager": ".settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
