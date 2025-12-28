from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class FileSettings(BaseSettings):
    """
    File Settings for kiarina.utils.file module.

    Environment variables:
        KIARINA_UTILS_FILE_LOCK_DIR: Custom lock directory path
        KIARINA_UTILS_FILE_LOCK_CLEANUP_ENABLED: Enable automatic cleanup
        KIARINA_UTILS_FILE_LOCK_MAX_AGE_HOURS: Maximum age for lock files in hours
    """

    model_config = SettingsConfigDict(env_prefix="KIARINA_UTILS_FILE_")

    lock_dir: str | None = Field(
        default=None,
        description="Lock file base directory. Default is <temp>/kiarina-utils-file-locks (user-specific on macOS, shared on Linux). Set custom path for explicit control.",
    )

    lock_cleanup_enabled: bool = Field(
        default=True,
        description="Enable automatic cleanup of old lock files",
    )

    lock_max_age_hours: int = Field(
        default=24,
        ge=1,
        description="Maximum age for lock files in hours before cleanup",
    )


settings_manager = SettingsManager(FileSettings)
