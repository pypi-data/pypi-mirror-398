def normalize_mime_type(mime_type: str) -> str:
    """
    Normalize MIME type

    Removes attributes (such as charset=utf-8) from MIME type,
    converts to lowercase, and returns the normalized MIME type.

    Args:
        mime_type (str): MIME type to normalize

    Returns:
        str: Normalized MIME type

    Examples:
        >>> normalize_mime_type("text/html; charset=utf-8")
        "text/html"

        >>> normalize_mime_type("APPLICATION/JSON")
        "application/json"

        >>> normalize_mime_type("image/jpeg; quality=85")
        "image/jpeg"
    """
    if not mime_type:
        return mime_type

    # Remove attributes if included in MIME type
    return mime_type.split(";")[0].strip().lower()
