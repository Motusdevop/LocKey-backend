from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOCKEY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LocKey Backend"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "lockey"
    db_user: str = "lockey"
    db_password: str = "lockey"

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
