from pydantic_settings import BaseSettings, SettingsConfigDict

from application.settings import ENV_FILE


class GeneralBaseSettings(BaseSettings):
    """Base settings for all settings in the project."""
    model_config = SettingsConfigDict(
        env_file='application/settings/.env',
        env_file_encoding="utf-8",
        arbitrary_types_allowed=True,
        extra='allow'
    )
