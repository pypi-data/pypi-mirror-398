from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FLUENTBIT_URL: str | None = None
    COMPONENT_NAME: str | None = "unknown"
    SYSTEM_NAME: str | None = "unknown"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@lru_cache
def get_settings():
    return Settings()
