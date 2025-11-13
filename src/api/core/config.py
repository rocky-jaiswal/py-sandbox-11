"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Async REST API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/mydb",
        alias="DATABASE_URL",
    )
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")

    # JWT Keys
    jwt_private_key_path: str = Field(default="keys/private_key.pem", alias="JWT_PRIVATE_KEY_PATH")
    jwt_public_key_path: str = Field(default="keys/public_key.pem", alias="JWT_PUBLIC_KEY_PATH")
    jwt_private_key_password: str | None = Field(default=None, alias="JWT_PRIVATE_KEY_PASSWORD")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
