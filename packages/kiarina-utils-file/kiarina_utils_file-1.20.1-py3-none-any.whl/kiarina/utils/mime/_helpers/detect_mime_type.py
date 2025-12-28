import logging
import os
from typing import BinaryIO, overload

from .._operations.detect_with_dictionary import detect_with_dictionary
from .._operations.detect_with_mimetypes import detect_with_mimetypes
from .._operations.detect_with_puremagic import detect_with_puremagic
from .._types.mime_detection_options import MimeDetectionOptions
from .apply_mime_alias import apply_mime_alias

logger = logging.getLogger(__name__)


@overload
def detect_mime_type(
    *,
    file_name_hint: str | os.PathLike[str] | None = None,
    raw_data: bytes | None = None,
    stream: BinaryIO | None = None,
    options: MimeDetectionOptions | None = None,
) -> str | None: ...


@overload
def detect_mime_type(
    *,
    file_name_hint: str | os.PathLike[str] | None = None,
    raw_data: bytes | None = None,
    stream: BinaryIO | None = None,
    options: MimeDetectionOptions | None = None,
    default: str,
) -> str: ...


def detect_mime_type(
    *,
    file_name_hint: str | os.PathLike[str] | None = None,
    raw_data: bytes | None = None,
    stream: BinaryIO | None = None,
    options: MimeDetectionOptions | None = None,
    default: str | None = None,
) -> str | None:
    """
    Detect the MIME type from file name and/or content.

    This function employs a pragmatic detection strategy that prioritizes
    explicit intent (file extension) over content analysis:

    Detection Strategy:
        1. **Extension-based detection** (if file_name_hint provided):
           - Custom dictionary lookup for complex extensions (.tar.gz, etc.)
           - Standard library mimetypes for common extensions
        2. **Content-based detection** (fallback):
           - puremagic analysis when extension is unavailable or unrecognized

    Philosophy:
        File extensions represent explicit user intent and should be trusted.
        Content analysis is used as a fallback when extension information is
        unavailable or insufficient. If you need to detect mismatches between
        extension and content, use a dedicated validation function.

    Args:
        file_name_hint (str | os.PathLike[str] | None): File name or path used for
            extension-based detection. This is prioritized over content analysis.
        raw_data (bytes | None): Raw binary data to analyze. Used as fallback when
            extension-based detection fails or file_name_hint is not provided.
        stream (BinaryIO | None): Binary file stream to analyze. Used as fallback
            when raw_data is None.
        options (MimeDetectionOptions | None): Optional configuration for detection behavior.
            All fields are optional and will be merged with default settings.
            See `MimeDetectionOptions` for available options.
        default (str | None): Default MIME type to return if detection fails. Default is None.

    Returns:
        (str | None): The detected and normalized MIME type, or default if detection fails.

    Note:
        At least one of file_name_hint, raw_data, or stream should be provided for
        meaningful detection.

    Examples:
        >>> # Extension-based detection (prioritized)
        >>> detect_mime_type(file_name_hint="document.md")
        "text/markdown"

        >>> # Content-based fallback
        >>> detect_mime_type(raw_data=b"\\x89PNG\\r\\n\\x1a\\n")
        "image/png"

        >>> # Extension takes precedence
        >>> detect_mime_type(
        ...     file_name_hint="document.md",  # Named .md
        ...     raw_data=png_bytes  # Actually PNG
        ... )
        "text/markdown"  # Trusts the extension

        >>> # With custom options
        >>> options = {"mime_aliases": {"application/x-yaml": "application/yaml"}}
        >>> detect_mime_type(file_name_hint="config.yaml", options=options)
        "application/yaml"

        >>> # With default value
        >>> detect_mime_type(file_name_hint="unknown.xyz", default="application/octet-stream")
        "application/octet-stream"
    """
    # Extract options
    options = options or {}
    mime_aliases = options.get("mime_aliases")
    custom_mime_types = options.get("custom_mime_types")
    multi_extensions = options.get("multi_extensions")
    archive_extensions = options.get("archive_extensions")
    compression_extensions = options.get("compression_extensions")
    encryption_extensions = options.get("encryption_extensions")

    # STEP 1: Extension-based detection (prioritized)
    if file_name_hint is not None:
        # Try custom dictionary (handles complex extensions)
        if mime_type := detect_with_dictionary(
            file_name_hint,
            custom_mime_types=custom_mime_types,
            multi_extensions=multi_extensions,
            archive_extensions=archive_extensions,
            compression_extensions=compression_extensions,
            encryption_extensions=encryption_extensions,
        ):
            return apply_mime_alias(mime_type, mime_aliases=mime_aliases)

        # Try standard mimetypes library
        if mime_type := detect_with_mimetypes(file_name_hint):
            return apply_mime_alias(mime_type, mime_aliases=mime_aliases)

    # STEP 2: Content-based detection (fallback)
    if raw_data is not None or stream is not None:
        if mime_type := detect_with_puremagic(
            raw_data=raw_data,
            stream=stream,
            file_name_hint=file_name_hint,
        ):
            return apply_mime_alias(mime_type, mime_aliases=mime_aliases)

    # If no MIME type is found, return default
    logger.debug(f"No MIME type found for file: {file_name_hint}")
    return default
