from typing import Any, Dict, Literal

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]


class DefaultSettings(BaseSettings):
    """Default settings."""

    # App
    FASTAPI_HOST: str = "localhost"
    FASTAPI_PORT: int = 8000
    BASE_URL: str | None = None
    OPENAPI_ENABLED: bool = True
    SCHEMA: str = "http"

    # Auth
    AUTH_BACKEND: str = "he_kit.authn.dummy.DummyAuthProvider"
    AUTH_BACKEND_SETTINGS: BaseSettings | dict = {}

    # Database
    DB_URL: str = "sqlite+aiosqlite:///default.db"
    DB_ECHO_SQL: bool = False

    # Internal
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: LogLevel = "INFO"
    LOG_JSON_FORMAT: bool = False

    # CORS
    CORS_ENABLED: bool = True
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOWED_ORIGINS: list[str] = ["*"]
    CORS_ALLOWED_METHODS: list[str] = ["*"]
    CORS_ALLOWED_HEADERS: list[str] = ["*"]

    def model_post_init(self, __context):
        """Automatically construct the BASE_URL if not present."""
        if self.BASE_URL is None:
            self.BASE_URL = f"{self.SCHEMA}://{self.FASTAPI_HOST}:{self.FASTAPI_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings(request: Request):
    """Expose settings for dependency injection."""
    return request.app.state.settings
