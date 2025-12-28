from ..settings import settings_manager


def apply_mime_alias(
    mime_type: str, *, mime_aliases: dict[str, str] | None = None
) -> str:
    """
    Apply a MIME type alias.

    MIME types obtained from puremagic or mimetypes may not be based on the latest RFC.
    This function applies configured MIME type aliases to normalize MIME types.
    For example, it converts "application/x-yaml" to "application/yaml".

    Args:
        mime_type (str): The original MIME type.
        mime_aliases (dict[str, str] | None): Optional dictionary of MIME type aliases.
            If None, the default aliases from settings will be used.

    Returns:
        (str): The normalized MIME type after applying the alias, or the original MIME type if no alias is found.
    """
    if mime_aliases is None:
        mime_aliases = settings_manager.settings.mime_aliases
    else:
        mime_aliases = {**settings_manager.settings.mime_aliases, **mime_aliases}

    return mime_aliases.get(mime_type, mime_type)
