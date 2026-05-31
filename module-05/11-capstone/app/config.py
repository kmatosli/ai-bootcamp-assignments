"""
config.py

Application configuration loaded from environment variables.
All settings have safe defaults for local development.
Never hardcode secrets here -- use .env.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./caduceus_dev.db"

    # JWT
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # App metadata
    app_name: str = "Caduceus Decision-Support API"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # CORS origins
    allowed_origins: list[str] = [
        "http://localhost:8501",   # Streamlit
        "http://localhost:3000",   # Next.js (future)
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
