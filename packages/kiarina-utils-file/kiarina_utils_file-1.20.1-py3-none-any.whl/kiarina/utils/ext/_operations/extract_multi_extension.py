import os
import pathlib

from .._utils.clean_url_path import clean_url_path
from ..settings import settings_manager


def extract_multi_extension(
    file_name_hint: str | os.PathLike[str],
    *,
    multi_extensions: set[str] | None = None,
    archive_extensions: set[str] | None = None,
    compression_extensions: set[str] | None = None,
    encryption_extensions: set[str] | None = None,
) -> str | None:
    """
    Extract multi-part file extensions from a file name hint.

    This function detects multi-part extensions such as `.tar.gz`, `.tar.bz2`, etc.
    It checks for known multi-part extensions first, and if not found,
    it dynamically detects multi-part extensions based on the file name hint.

    Args:
        file_name_hint (str | os.PathLike[str]): File name hint
        multi_extensions (set[str] | None): Set of recognized multi-part extensions.
            If provided, it will be merged with the default settings.
        archive_extensions (set[str] | None): Set of archive-related extensions.
            If provided, it will be merged with the default settings.
        compression_extensions (set[str] | None): Set of compression-related extensions.
            If provided, it will be merged with the default settings.
        encryption_extensions (set[str] | None): Set of encryption-related extensions.
            If provided, it will be merged with the default settings.

    Returns:
        str | None: Multi-part extension. Returns None if detection is not possible.
    """
    file_name_hint = os.path.expanduser(os.path.expandvars(os.fspath(file_name_hint)))

    if not file_name_hint:
        return None

    # Remove parameters and fragments for URL format
    file_name_hint = clean_url_path(file_name_hint)

    # Get filename and convert to lowercase
    filename_lower = pathlib.Path(file_name_hint).name.lower()

    # Get settings and merge with provided arguments
    settings = settings_manager.settings

    if multi_extensions is None:
        multi_exts = settings.multi_extensions
    else:
        multi_exts = settings.multi_extensions | multi_extensions

    if archive_extensions is None:
        archive_exts = settings.archive_extensions
    else:
        archive_exts = settings.archive_extensions | archive_extensions

    if compression_extensions is None:
        compression_exts = settings.compression_extensions
    else:
        compression_exts = settings.compression_extensions | compression_extensions

    if encryption_extensions is None:
        encryption_exts = settings.encryption_extensions
    else:
        encryption_exts = settings.encryption_extensions | encryption_extensions

    # Check known multi-part extensions with priority
    for multi_ext in sorted(multi_exts, key=len, reverse=True):
        if filename_lower.endswith(multi_ext):
            return multi_ext.lower()

    # Dynamically detect multi-part extensions
    parts = filename_lower.split(".")

    if len(parts) >= 3:  # At least name.ext1.ext2 format
        # Check extension combinations from the end
        max_parts = (
            settings.max_multi_extension_parts + 1
        )  # +1 because range is exclusive

        for i in range(2, min(len(parts), max_parts)):
            candidate_ext = "." + ".".join(parts[-i:])
            ext_parts = candidate_ext[1:].split(".")

            # Check archive + compression/encryption patterns
            if len(ext_parts) >= 2:
                first_ext = f".{ext_parts[0]}"
                remaining_exts = [f".{ext}" for ext in ext_parts[1:]]

                # Pattern starting with .tar followed by compression or encryption extensions
                if first_ext in archive_exts and any(
                    (ext in compression_exts or ext in encryption_exts)
                    for ext in remaining_exts
                ):
                    return candidate_ext.lower()

    return None
