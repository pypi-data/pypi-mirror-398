from ..settings import settings_manager


def get_default_encoding() -> str:
    """
    Get the default encoding

    Returns:
        str: Default encoding
    """
    return settings_manager.settings.default_encoding
