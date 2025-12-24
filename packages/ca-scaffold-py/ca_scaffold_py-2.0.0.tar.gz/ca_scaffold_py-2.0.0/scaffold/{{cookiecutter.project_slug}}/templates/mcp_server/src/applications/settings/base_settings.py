from pydantic_settings import BaseSettings, SettingsConfigDict

from src.applications.settings import ENV_FILE


class GeneralBaseSettings(BaseSettings):
    """Base settings for all settings in the project."""
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        arbitrary_types_allowed=True,
    )
