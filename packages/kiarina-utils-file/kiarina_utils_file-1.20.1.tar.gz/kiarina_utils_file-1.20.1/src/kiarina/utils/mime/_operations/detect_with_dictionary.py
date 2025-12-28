import logging
import os

import kiarina.utils.ext as ke

from ..settings import settings_manager

logger = logging.getLogger(__name__)


def detect_with_dictionary(
    file_name_hint: str | os.PathLike[str],
    *,
    custom_mime_types: dict[str, str] | None = None,
    multi_extensions: set[str] | None = None,
    archive_extensions: set[str] | None = None,
    compression_extensions: set[str] | None = None,
    encryption_extensions: set[str] | None = None,
) -> str | None:
    """
    Detect MIME type using a dictionary of file extensions.

    This function attempts to determine the MIME type based on the file extension extracted from the provided file name hint.
    It uses a custom MIME type dictionary if provided, or falls back to the default settings.

    Args:
        file_name_hint (str | os.PathLike[str]): File name or path to detect MIME type.
            The extension will be extracted from this hint.
        custom_mime_types (dict[str, str] | None): Custom extension to MIME type mapping.
            If provided, it will be merged with the default settings, with custom values taking precedence.
        multi_extensions (set[str] | None): Set of recognized multi-part extensions.
            See `kiarina.utils.ext.extract_extension` for details.
        archive_extensions (set[str] | None): Set of archive-related extensions.
            See `kiarina.utils.ext.extract_extension` for details.
        compression_extensions (set[str] | None): Set of compression-related extensions.
            See `kiarina.utils.ext.extract_extension` for details.
        encryption_extensions (set[str] | None): Set of encryption-related extensions.
            See `kiarina.utils.ext.extract_extension` for details.

    Returns:
        (str | None): Detected MIME type or None if not found.
    """
    # Extract the file extension from the file name hint
    ext = ke.extract_extension(
        file_name_hint,
        multi_extensions=multi_extensions,
        archive_extensions=archive_extensions,
        compression_extensions=compression_extensions,
        encryption_extensions=encryption_extensions,
    )

    if not ext:
        return None

    # Detect MIME type using custom MIME types
    if custom_mime_types is not None and ext in custom_mime_types:
        return custom_mime_types[ext]

    # Detect MIME type using default settings
    settings = settings_manager.settings

    if ext in settings.custom_mime_types:
        return settings.custom_mime_types[ext]

    return None
