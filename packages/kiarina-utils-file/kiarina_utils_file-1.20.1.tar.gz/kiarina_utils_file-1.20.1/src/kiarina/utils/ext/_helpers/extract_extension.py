import logging
import os
import pathlib
from typing import overload

from .._operations.extract_multi_extension import extract_multi_extension
from .._utils.clean_url_path import clean_url_path

logger = logging.getLogger(__name__)


@overload
def extract_extension(
    file_name_hint: str | os.PathLike[str],
    *,
    multi_extensions: set[str] | None = None,
    archive_extensions: set[str] | None = None,
    compression_extensions: set[str] | None = None,
    encryption_extensions: set[str] | None = None,
) -> str | None: ...


@overload
def extract_extension(
    file_name_hint: str | os.PathLike[str],
    *,
    multi_extensions: set[str] | None = None,
    archive_extensions: set[str] | None = None,
    compression_extensions: set[str] | None = None,
    encryption_extensions: set[str] | None = None,
    default: str,
) -> str: ...


def extract_extension(
    file_name_hint: str | os.PathLike[str],
    *,
    multi_extensions: set[str] | None = None,
    archive_extensions: set[str] | None = None,
    compression_extensions: set[str] | None = None,
    encryption_extensions: set[str] | None = None,
    default: str | None = None,
) -> str | None:
    """
    Extract file extension from a file name hint.

    This function extracts the file extension from a file name hint based on string
    analysis only. It does NOT read or access the actual file on the filesystem.

    1. If the file name hint contains a URL, it removes parameters and fragments.
    2. It checks for multi-part extensions first. (e.g., .tar.gz, .tar.gz.gpg).
    3. If no multi-part extension is found, it returns the regular file extension.
    4. If no extension can be determined, it returns the default value or None.

    Args:
        file_name_hint (str | os.PathLike[str]): File name hint. This function
            performs string-based analysis only and does not read the actual file.
        multi_extensions (set[str] | None): Set of recognized multi-part extensions.
            If provided, it will be merged with the default settings.
        archive_extensions (set[str] | None): Set of archive-related extensions.
            If provided, it will be merged with the default settings.
        compression_extensions (set[str] | None): Set of compression-related extensions.
            If provided, it will be merged with the default settings.
        encryption_extensions (set[str] | None): Set of encryption-related extensions.
            If provided, it will be merged with the default settings.
        default (str | None): Default extension to return if extraction fails. Default is None.

    Returns:
        str | None: File extension. Returns default if extraction is not possible.

    Note:
        This function does not access the filesystem or read file contents.
        It only analyzes the provided file name string.
    """
    # Normalize the file name hint
    file_name_hint = os.path.expanduser(os.path.expandvars(os.fspath(file_name_hint)))

    if not file_name_hint:
        return default

    # Remove parameters and fragments for URL format
    file_name_hint = clean_url_path(file_name_hint)

    # Extract multi-part extensions first
    if multi_ext := extract_multi_extension(
        file_name_hint,
        multi_extensions=multi_extensions,
        archive_extensions=archive_extensions,
        compression_extensions=compression_extensions,
        encryption_extensions=encryption_extensions,
    ):
        return multi_ext

    # If no multi-part extension found, get the regular extension
    if ext := pathlib.Path(file_name_hint).suffix:
        return ext.lower()

    # If no extension is found, return default
    logger.debug(f"No extension found for file name hint: {file_name_hint}")
    return default
