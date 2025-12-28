from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class MIMESettings(BaseSettings):
    """
    MIME Settings
    """

    model_config = SettingsConfigDict(env_prefix="KIARINA_UTILS_MIME_")

    custom_mime_types: dict[str, str] = Field(
        default_factory=lambda: {
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ts": "application/typescript",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".yaml": "application/yaml",
            ".yml": "application/yaml",
        }
    )
    """
    Custom MIME types mapping.

    Dictionary for obtaining MIME types based on file extensions.

    - Key: File extension
    - Value: MIME type
    """

    mime_aliases: dict[str, str] = Field(
        default_factory=lambda: {
            "application/x-yaml": "application/yaml",  # RFC 9512
        }
    )
    """
    MIME type aliases.

    Dictionary for obtaining alternative MIME types based on existing types.

    - Key: Original MIME type (values returned by puremagic or mimetypes)
    - Value: Alternative MIME type
    """

    hash_algorithm: str = "sha256"
    """Hash algorithm"""


settings_manager = SettingsManager(MIMESettings)
"""MIME settings manager"""
