import logging
from typing import overload

from .._operations.detect_with_dictionary import detect_with_dictionary
from .._operations.detect_with_mimetypes import detect_with_mimetypes

logger = logging.getLogger(__name__)


@overload
def detect_extension(
    mime_type: str,
    *,
    custom_extensions: dict[str, str] | None = None,
) -> str | None: ...


@overload
def detect_extension(
    mime_type: str,
    *,
    custom_extensions: dict[str, str] | None = None,
    default: str,
) -> str: ...


def detect_extension(
    mime_type: str,
    *,
    custom_extensions: dict[str, str] | None = None,
    default: str | None = None,
) -> str | None:
    """
    Detect the file extension based on MIME type.

    This function attempts to determine the file extension using a combination of:
    1. A custom MIME type to extension mapping.
    2. The built-in mimetypes library.

    Args:
        mime_type (str): MIME type to convert to an extension.
        custom_extensions (dict[str, str] | None): Custom MIME type to extension mapping.
            If provided, it will be merged with the default settings, with custom values taking precedence.
        default (str | None): Default extension to return if detection fails. Default is None.

    Returns:
        (str | None): Extension (lowercase, including the dot). Returns default if detection fails.
    """
    # Try to detect extension using custom dictionary
    if ext := detect_with_dictionary(mime_type, custom_extensions=custom_extensions):
        return ext

    # Try to detect extension using mimetypes library
    if ext := detect_with_mimetypes(mime_type):
        return ext

    # If no extension is found, return default
    logger.debug(f"No extension found for MIME type: {mime_type}")
    return default
