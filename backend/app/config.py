"""
Agent Control Room — Backend Configuration
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──────────────────────────────────────────
    APP_NAME: str = "Agent Control Room"
    APP_VERSION: str = "0.1.0"
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────
    POSTGRES_USER: str = "acr_user"
    POSTGRES_PASSWORD: str = "acr_secret_password"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "agentcontrolroom"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"
    DRAMATIQ_BROKER_URL: str = "redis://redis:6379/1"

    # ── CORS ─────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Data Retention ───────────────────────────────
    DEFAULT_RETENTION_DAYS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
