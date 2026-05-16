"""
app/config.py

Central settings management for CollabFlow.
Uses pydantic-settings to load and validate all environment variables from .env file.
Access anywhere via: from app.config import settings
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    """
    All application settings loaded from environment variables / .env file.
    Pydantic automatically validates types and raises errors on missing required vars.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",             # ignore extra vars in .env
    )

    # ---- Application ----
    APP_NAME: str = "CollabFlow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ---- Server ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---- Database (PostgreSQL) ----
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "collabflow"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        """Async database URL for SQLAlchemy (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync database URL for Alembic migrations (psycopg2 driver)."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ---- Redis ----
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ---- JWT Auth ----
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- CORS ----
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # ---- File Upload ----
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads/"
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,image/gif,application/pdf,text/plain"

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def ALLOWED_FILE_TYPES_LIST(self) -> List[str]:
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    # ---- Rate Limiting ----
    RATE_LIMIT_PER_MINUTE: int = 60

    # ---- Email ----
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM: str = "noreply@collabflow.com"

    # ---- Celery ----
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/collabflow.log"

    # ---- Derived Flags ----
    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Using lru_cache means .env is only read once — not on every import.
    """
    return Settings()


# Single shared instance — import this everywhere
settings = get_settings()