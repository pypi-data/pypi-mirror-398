from .._utils.normalize_newlines import normalize_newlines
from ..settings import settings_manager
from .detect_encoding import detect_encoding


def decode_binary_to_text(
    raw_data: bytes,
    *,
    use_nkf: bool | None = None,
    fallback_encodings: list[str] | None = None,
    default_encoding: str | None = None,
) -> str:
    """
    Decode binary data to text data

    Args:
        raw_data (bytes): Binary data to decode
        use_nkf (bool | None): Whether to use nkf command for encoding detection.
            If None, uses setting value or auto-detection.
        fallback_encodings (list[str] | None): List of encodings to try during fallback
            detection. If None, uses setting value.
        default_encoding (str | None): Default encoding when all detection methods fail.
            If None, uses setting value.

    Returns:
        str: Decoded text data
    """
    if default_encoding is None:
        default_encoding = settings_manager.settings.default_encoding

    encoding = detect_encoding(
        raw_data, use_nkf=use_nkf, fallback_encodings=fallback_encodings
    )

    if encoding is None:
        encoding = default_encoding

    if encoding == "ascii":
        # ASCII is compatible with UTF-8, so treat it as UTF-8 for convenience
        encoding = "utf-8"

    text = raw_data.decode(encoding, errors="replace")

    # Universal newlines mode
    return normalize_newlines(text)
