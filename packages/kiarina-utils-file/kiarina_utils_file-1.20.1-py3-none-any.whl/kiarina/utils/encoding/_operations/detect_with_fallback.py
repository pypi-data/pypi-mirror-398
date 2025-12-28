from ..settings import settings_manager


def detect_with_fallback(
    raw_data: bytes,
    *,
    fallback_encodings: list[str] | None = None,
) -> str | None:
    """
    Detect encoding by trying fallback encoding list in order

    Retrieves fallback encoding list from settings and tries them sequentially.
    For large files, only a sample from the beginning is used for efficiency.

    Args:
        raw_data (bytes): Binary data to detect encoding from
        fallback_encodings (list[str] | None): List of encodings to try during fallback
            detection. If None, uses setting value.

    Returns:
        (str | None): Detected encoding name, or None if detection fails
    """
    if not raw_data:
        return None

    if fallback_encodings is None:
        fallback_encodings = settings_manager.settings.fallback_encodings

    # Use sample for large files to improve performance
    max_size = settings_manager.settings.max_sample_size

    if len(raw_data) > max_size:
        sample_data = raw_data[:max_size]
    else:
        sample_data = raw_data

    for enc in fallback_encodings:
        try:
            sample_data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue

    return None
