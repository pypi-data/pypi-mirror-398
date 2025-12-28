def normalize_newlines(text: str) -> str:
    """
    Normalize newline characters in text (Universal newlines mode)

    Converts Windows-style (\r\n) and Mac-style (\r) newline characters
    to Unix-style (\n) newlines.

    Args:
        text (str): Text to normalize

    Returns:
        str: Text with normalized newline characters

    Examples:
        >>> normalize_newlines("line1\r\nline2\rline3\n")
        "line1\nline2\nline3\n"

        >>> normalize_newlines("Hello\r\nWorld")
        "Hello\nWorld"
    """
    if not text:
        return text

    # Process Windows-style (\r\n) first, then Mac-style (\r)
    return text.replace("\r\n", "\n").replace("\r", "\n")
