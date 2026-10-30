"""
Core application settings using Pydantic Settings.
"""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Parking SaaS ALPR"
    SECRET_KEY: str = "change-this-to-a-super-secret-key-in-production-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # URL pública do frontend (usada para montar o link de recuperação de senha)
    FRONTEND_URL: str = "http://localhost:4200"

    # SMTP (opcional). Sem SMTP_HOST, e-mails não são enviados.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@parkingsaas.local"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "parkingsaas_db"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/parkingsaas_db"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://localhost:3000",
        "http://127.0.0.1:4200",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
