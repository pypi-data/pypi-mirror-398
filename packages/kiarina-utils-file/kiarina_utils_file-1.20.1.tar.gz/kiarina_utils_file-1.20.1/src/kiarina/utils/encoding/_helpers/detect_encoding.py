from .._operations.detect_with_charset_normalizer import detect_with_charset_normalizer
from .._operations.detect_with_fallback import detect_with_fallback
from .._operations.detect_with_nkf import detect_with_nkf
from .._operations.should_use_nkf import should_use_nkf
from ..settings import settings_manager


def detect_encoding(
    raw_data: bytes,
    *,
    use_nkf: bool | None = None,
    confidence_threshold: float | None = None,
    fallback_encodings: list[str] | None = None,
) -> str | None:
    """
    Detect encoding from binary data

    Attempts detection in the following order based on settings:
    1. nkf (if use_nkf is True or auto-detection returns True)
    2. charset_normalizer
    3. Try fallback encoding list in order
    4. Return None (if detection fails)

    Args:
        raw_data (bytes): Binary data to detect encoding from
        use_nkf (bool | None): Whether to use nkf command for detection.
            If None, uses setting value or auto-detection.
        confidence_threshold (float | None): Minimum confidence threshold for charset_normalizer.
            If None, uses setting value.
        fallback_encodings (list[str] | None): List of encodings to try during fallback
            detection. If None, uses setting value.

    Returns:
        (str | None): Detected encoding name (lowercase), or None

    Note:
        charset_normalizer may misidentify Japanese encodings (shift_jis as cp932,
        euc-jp as big5). Use nkf for more accurate Japanese encoding detection.
    """
    if use_nkf is None:
        use_nkf = settings_manager.settings.use_nkf

    if use_nkf is None:
        use_nkf = should_use_nkf()

    # 1. Detection using nkf
    if use_nkf:
        if encoding := detect_with_nkf(raw_data):
            return encoding

    # 2. Detection using charset_normalizer
    if encoding := detect_with_charset_normalizer(
        raw_data, confidence_threshold=confidence_threshold
    ):
        return encoding

    # 3. Try fallback encoding list in order
    if encoding := detect_with_fallback(
        raw_data, fallback_encodings=fallback_encodings
    ):
        return encoding

    return None
