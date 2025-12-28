from mimetypes import guess_extension

from .._utils.normalize_mime_type import normalize_mime_type


def detect_with_mimetypes(mime_type: str) -> str | None:
    """
    Detect the file extension based on MIME type using the mimetypes library.

    This function attempts to determine the file extension using the built-in mimetypes library.

    Args:
        mime_type (str): MIME type to convert to an extension.

    Returns:
        (str | None): Extension (lowercase, including the dot)
    """
    mime_type = normalize_mime_type(mime_type)

    if ext := guess_extension(mime_type, strict=False):
        return ext.lower()

    return None
