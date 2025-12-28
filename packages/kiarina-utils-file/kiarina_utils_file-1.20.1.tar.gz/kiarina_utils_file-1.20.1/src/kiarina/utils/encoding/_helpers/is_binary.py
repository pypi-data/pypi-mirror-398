from .detect_encoding import detect_encoding


def is_binary(
    raw_data: bytes,
    *,
    use_nkf: bool | None = None,
    fallback_encodings: list[str] | None = None,
) -> bool:
    """
    Determine if the data is binary data

    Args:
        raw_data (bytes): Data to check. Empty bytes return False.
        use_nkf (bool | None): Whether to use nkf command for detection.
            If None, uses setting value or auto-detection.
        fallback_encodings (list[str] | None): List of encodings to try during fallback
            detection. If None, uses setting value.

    Returns:
        bool: True if binary data, False if text data (including empty bytes)
    """
    if not raw_data:
        return False

    encoding = detect_encoding(
        raw_data, use_nkf=use_nkf, fallback_encodings=fallback_encodings
    )

    return encoding is None
