from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class EncodingSettings(BaseSettings):
    """
    Encoding detection and processing settings
    """

    model_config = SettingsConfigDict(env_prefix="KIARINA_UTILS_ENCODING_")

    use_nkf: bool | None = None
    """
    Whether to use the nkf command for encoding detection

    If None, nkf will be automatically used when available in Japanese environments.
    """

    fallback_encodings: list[str] = Field(
        default_factory=lambda: ["utf-8", "shift_jis", "euc-jp", "iso2022_jp"]
    )
    """
    List of encodings to try during fallback detection

    Note: ASCII is not included as it's a subset of UTF-8 and would be
    redundant. UTF-8 detection will handle ASCII text correctly.
    """

    default_encoding: str = "utf-8"
    """Default encoding when all detection methods fail"""

    max_sample_size: int = 8192
    """Maximum bytes to sample for encoding detection (default: 8KB)"""

    charset_normalizer_confidence_threshold: float = 0.6
    """Minimum confidence threshold for charset_normalizer detection (default: 0.6)"""


settings_manager = SettingsManager(EncodingSettings)
"""Encoding settings manager"""
