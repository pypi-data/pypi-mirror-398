import os


def clean_url_path(file_path: str | os.PathLike[str]) -> str:
    """
    Remove parameters and fragments from URL-formatted paths

    For URL format (containing "://"), removes query parameters (after ?)
    and fragments (after #) to return a clean path.

    Args:
        file_path (str | os.PathLike[str]): Path to clean

    Returns:
        str: Clean path

    Examples:
        >>> clean_url_path("https://example.com/file.txt?param=value#section")
        "https://example.com/file.txt"

        >>> clean_url_path("file:///path/to/file.txt?query=test")
        "file:///path/to/file.txt"

        >>> clean_url_path("/local/path/file.txt")
        "/local/path/file.txt"
    """
    file_path = os.path.expanduser(os.path.expandvars(os.fspath(file_path)))

    if not file_path:
        return file_path

    if "://" not in file_path:
        return file_path

    if not any(ch in file_path for ch in ("?", "#")):
        return file_path

    # Remove parameters and fragments for URL format
    return file_path.split("?", 1)[0].split("#", 1)[0]
