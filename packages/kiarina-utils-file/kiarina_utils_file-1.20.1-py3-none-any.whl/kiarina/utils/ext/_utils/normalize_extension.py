def normalize_extension(extension: str) -> str:
    """
    Normalize extension by ensuring it starts with a dot and is lowercase.

    Args:
        extension (str): Extension to normalize

    Returns:
        str: Normalized extension (lowercase, starting with dot),
             or empty string if input is empty

    Examples:
        >>> normalize_extension("txt")
        ".txt"
        >>> normalize_extension(".TXT")
        ".txt"
        >>> normalize_extension(" .Custom ")
        ".custom"
        >>> normalize_extension("")
        ""
        >>> normalize_extension("   ")
        ""
    """
    extension = extension.strip().lower()

    # Return empty string if input is empty or whitespace only
    if not extension:
        return ""

    if not extension.startswith("."):
        extension = f".{extension}"

    return extension
