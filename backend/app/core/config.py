from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/secure_messenger"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Master key for encrypting user keys (32 bytes hex = 64 chars)
    MASTER_KEY: str = "0" * 64

    # CORS
    CORS_ORIGINS: str = "*"

    @field_validator("MASTER_KEY", mode="before")
    @classmethod
    def ensure_master_key_non_empty(cls, v: Optional[str]) -> str:
        """Use default 64 hex zeros if MASTER_KEY is missing or empty (e.g. in Docker without .env)."""
        if not v or not str(v).strip():
            return "0" * 64
        return str(v).strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
