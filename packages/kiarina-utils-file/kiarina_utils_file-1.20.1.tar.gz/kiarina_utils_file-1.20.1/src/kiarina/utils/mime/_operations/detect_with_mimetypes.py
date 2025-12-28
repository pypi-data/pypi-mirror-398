import logging
import os
from mimetypes import guess_type

logger = logging.getLogger(__name__)


def detect_with_mimetypes(file_name_hint: str | os.PathLike[str]) -> str | None:
    """
    Detect MIME type using mimetypes library.

    Args:
        file_name_hint (str | os.PathLike[str]): File name hint for MIME type detection.

    Returns:
        str | None: Detected MIME type or None if not found.
    """
    mime_type, _ = guess_type(file_name_hint, strict=False)

    return mime_type
