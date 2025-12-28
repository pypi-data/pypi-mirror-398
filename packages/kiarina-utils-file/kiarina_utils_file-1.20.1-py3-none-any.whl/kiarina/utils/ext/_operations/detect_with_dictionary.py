from .._utils.normalize_extension import normalize_extension
from .._utils.normalize_mime_type import normalize_mime_type
from ..settings import settings_manager


def detect_with_dictionary(
    mime_type: str,
    *,
    custom_extensions: dict[str, str] | None = None,
) -> str | None:
    """
    Detect the file extension based on MIME type using a dictionary.

    This function attempts to determine the file extension using a custom MIME type to extension mapping.
    Extensions in the dictionary can be provided with or without the leading dot - it will be automatically added if missing.

    Args:
        mime_type (str): MIME type to convert to an extension.
        custom_extensions (dict[str, str] | None): Custom MIME type to extension mapping.
            If provided, it will be merged with the default settings, with custom values taking precedence.
            Extensions can be provided with or without the leading dot (e.g., both ".txt" and "txt" are acceptable).

    Returns:
        (str | None): Extension (lowercase, including the dot)
    """
    mime_type = normalize_mime_type(mime_type)

    if custom_extensions is not None and mime_type in custom_extensions:
        return normalize_extension(custom_extensions[mime_type])

    settings = settings_manager.settings

    if mime_type in settings.custom_extensions:
        return normalize_extension(settings.custom_extensions[mime_type])

    return None
