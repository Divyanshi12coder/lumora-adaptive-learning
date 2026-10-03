"""Application settings, loaded from environment variables (12-factor style).

Nothing secret is hard-coded here. In production `JWT_SECRET` must be set;
the app refuses to start with the development default when ENVIRONMENT=production.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Lumora"
    environment: Literal["development", "test", "production"] = "development"

    # --- Database -----------------------------------------------------------
    # PostgreSQL (+pgvector) in production/docker. SQLite is supported for
    # quick local runs and the unit-test suite (vector search falls back to numpy).
    database_url: str = "sqlite:///./lumora.db"

    # --- Auth ---------------------------------------------------------------
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24

    # --- HTTP ---------------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_request_bytes: int = 6 * 1024 * 1024
    max_upload_bytes: int = 5 * 1024 * 1024
    rate_limit_enabled: bool = True

    # --- AI -----------------------------------------------------------------
    ai_provider: Literal["demo", "openai", "anthropic"] = "demo"
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_timeout_seconds: float = 45.0

    # --- RAG ----------------------------------------------------------------
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 384
    rag_top_k: int = 4
    chunk_size_words: int = 120
    chunk_overlap_words: int = 30

    # --- ML -----------------------------------------------------------------
    ml_artifact_dir: str = Field(default="app/ml/artifacts")
    ml_min_real_samples: int = 300

    # --- Seeding ------------------------------------------------------------
    seed_on_startup: bool = True

    @field_validator("database_url")
    @classmethod
    def _normalise_db_url(cls, v: str) -> str:
        # Render / Heroku style URLs use postgres:// - SQLAlchemy needs a driver.
        if v.startswith("postgres://"):
            v = "postgresql+psycopg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    @model_validator(mode="after")
    def _check_production(self) -> "Settings":
        if self.environment == "production" and self.jwt_secret == DEV_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set to a strong random value in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def resolved_ai_model(self) -> str:
        if self.ai_model:
            return self.ai_model
        return {
            "openai": "gpt-4.1-mini",
            "anthropic": "claude-opus-5-5",
            "demo": "lumora-demo-1",
        }[self.ai_provider]


@lru_cache
def get_settings() -> Settings:
    return Settings()
