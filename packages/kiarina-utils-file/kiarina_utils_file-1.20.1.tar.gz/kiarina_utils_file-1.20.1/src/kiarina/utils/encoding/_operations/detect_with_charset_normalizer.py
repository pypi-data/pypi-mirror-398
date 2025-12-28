import logging

from charset_normalizer import detect

from ..settings import settings_manager

logger = logging.getLogger(__name__)


def detect_with_charset_normalizer(
    raw_data: bytes, *, confidence_threshold: float | None = None
) -> str | None:
    """
    Detect encoding using the charset_normalizer library

    Args:
        raw_data (bytes): Binary data to detect encoding from
        confidence_threshold (float | None): Minimum confidence threshold for detection.
            If None, uses setting value.

    Returns:
        (str | None): Detected encoding name (lowercase), or None if detection fails

    Note:
        charset_normalizer automatically performs sampling for performance optimization.
        The detect() function internally uses from_bytes() with default settings:
        - steps=5, chunk_size=512 (max 2,560 bytes sampled)
        - No manual sampling implementation is needed for large files
    """
    if not raw_data:
        return None

    if confidence_threshold is None:
        confidence_threshold = (
            settings_manager.settings.charset_normalizer_confidence_threshold
        )

    # charset_normalizer's detect() automatically samples data for efficiency
    # (default: 5 chunks × 512 bytes = max 2,560 bytes)
    result = detect(raw_data)

    if (
        result["encoding"]
        and result["confidence"]
        and result["confidence"] >= confidence_threshold
    ):
        return result["encoding"].lower()

    return None
