"""
MIME type detection and processing utilities.

This module provides comprehensive functionality for:
- Detecting MIME types from file names and binary data
- Creating MIME-typed data containers (MIMEBlob)
- Normalizing MIME types using configurable aliases
- Multi-stage detection using extension mapping and content analysis

Key Features:
    - **Extension-based detection**: Prioritizes file extensions as explicit user intent
    - **Content-based detection**: Uses puremagic as fallback for unknown extensions
    - **Complex extensions**: Supports multi-part extensions (.tar.gz, .tar.gz.gpg)
    - **MIME type normalization**: Applies configurable aliases for consistency
    - **Data container**: MIMEBlob class for handling MIME-typed binary data

Detection Strategy:
    1. Extension-based detection (prioritized):
       - Custom dictionary lookup for complex extensions
       - Standard library mimetypes for common extensions
    2. Content analysis using puremagic (fallback)
    3. Automatic MIME type alias normalization

Philosophy:
    File extensions represent explicit user intent and should be trusted.
    Content analysis is used as a fallback when extension information is
    unavailable or insufficient.

Examples:
    >>> import kiarina.utils.mime as km
    >>>
    >>> # Detect MIME type from file name (prioritized)
    >>> mime_type = km.detect_mime_type(file_name_hint="document.md")
    >>> print(mime_type)  # "text/markdown"
    >>>
    >>> # Detect from binary data (fallback)
    >>> mime_type = km.detect_mime_type(raw_data=jpeg_bytes)
    >>> print(mime_type)  # "image/jpeg"
    >>>
    >>> # Extension takes precedence
    >>> mime_type = km.detect_mime_type(
    ...     file_name_hint="document.md",
    ...     raw_data=png_bytes  # Actually PNG
    ... )
    >>> print(mime_type)  # "text/markdown" (trusts the extension)
    >>>
    >>> # Create MIMEBlob from data
    >>> blob = km.create_mime_blob(jpeg_bytes)
    >>> print(blob.mime_type)  # "image/jpeg"
    >>> print(blob.ext)        # ".jpg"
    >>>
    >>> # Create MIMEBlob from text
    >>> blob = km.MIMEBlob("text/plain", raw_text="Hello World")
    >>> print(blob.raw_base64_url)  # "data:text/plain;base64,SGVsbG8gV29ybGQ="

Configuration:
    MIME type detection behavior can be customized through environment variables:
    - KIARINA_UTILS_MIME_CUSTOM_MIME_TYPES: Custom extension to MIME type mapping
    - KIARINA_UTILS_MIME_MIME_ALIASES: MIME type aliases for normalization
    - KIARINA_UTILS_MIME_HASH_ALGORITHM: Hash algorithm for MIMEBlob (default: sha256)

Note:
    For optimal content-based detection, install the optional puremagic dependency.
    Without it, detection falls back to extension-based methods only.
"""

# pip install kiarina-utils-mime
import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._helpers.apply_mime_alias import apply_mime_alias
    from ._helpers.create_mime_blob import create_mime_blob
    from ._helpers.detect_mime_type import detect_mime_type
    from ._models.mime_blob import MIMEBlob
    from ._types.mime_detection_options import MimeDetectionOptions
    from .settings import settings_manager

__version__ = "1.0.0"

__all__ = [
    # .helpers
    "apply_mime_alias",
    "create_mime_blob",
    "detect_mime_type",
    # .model
    "MIMEBlob",
    # .settings
    "settings_manager",
    # .types
    "MimeDetectionOptions",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # .helpers
        "apply_mime_alias": "._helpers.apply_mime_alias",
        "create_mime_blob": "._helpers.create_mime_blob",
        "detect_mime_type": "._helpers.detect_mime_type",
        # .model
        "MIMEBlob": "._models.mime_blob",
        # .settings
        "settings_manager": ".settings",
        # .types
        "MimeDetectionOptions": "._types.mime_detection_options",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
