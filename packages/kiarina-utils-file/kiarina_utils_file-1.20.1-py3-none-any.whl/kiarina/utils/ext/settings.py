from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class ExtSettings(BaseSettings):
    """
    Extension Settings
    """

    model_config = SettingsConfigDict(env_prefix="KIARINA_UTILS_EXT_")

    custom_extensions: dict[str, str] = Field(
        default_factory=lambda: {
            "application/yaml": ".yaml",
            "image/jpeg": ".jpg",
            "text/html": ".html",
            "text/plain": ".txt",
            "text/xml": ".xml",
        }
    )
    """
    Custom extension dictionary

    Dictionary for obtaining extensions based on MIME types.

    - Key: MIME type
    - Value: Extension
    """

    multi_extensions: set[str] = Field(
        default_factory=lambda: {
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
            ".tar.lz",
            ".tar.z",
            ".tar.lzma",
            ".tar.lzo",
            ".tar.zst",
            ".tar.gz.gpg",
            ".tar.bz2.gpg",
            ".tar.xz.gpg",
        }
    )
    """
    Set of recognized multi-part extensions

    List of extensions recognized as multi-part extensions when extracting extensions from file paths.
    Includes double extensions (.tar.gz) and triple extensions (.tar.gz.gpg).
    """

    compression_extensions: set[str] = Field(
        default_factory=lambda: {
            ".gz",
            ".bz2",
            ".xz",
            ".lz",
            ".z",
            ".lzma",
            ".lzo",
            ".zst",
        }
    )
    """Set of compression-related extensions"""

    archive_extensions: set[str] = Field(default_factory=lambda: {".tar"})
    """Set of archive-related extensions"""

    encryption_extensions: set[str] = Field(default_factory=lambda: {".gpg", ".pgp"})
    """Set of encryption-related extensions"""

    max_multi_extension_parts: int = Field(default=4)
    """Maximum number of parts for multi-extension detection (e.g., 4 for .tar.gz.gpg)"""


settings_manager = SettingsManager(ExtSettings)
"""Ext settings manager"""
