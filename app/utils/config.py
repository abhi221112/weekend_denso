"""
Application Configuration
==========================
Centralised settings loaded from the .env file via python-dotenv.

Usage:
    from app.utils.config import settings

    print(settings.DB_SERVER)
    print(settings.SECRET_KEY)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Database ─────────────────────────────────────────────────
    DB_SERVER: str = os.getenv("DB_SERVER", "")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "DTraceProddb")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_PORT: int = int(os.getenv("DB_PORT", "1433"))
    DB_DRIVER: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    USE_WINDOWS_AUTH: bool = os.getenv("USE_WINDOWS_AUTH", "true").lower() == "true"

    # ── JWT / Auth ────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "d-trace-supplier-end-user-api-secret-key-2026"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")  # 7 days
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # ── Application ───────────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "Resolute API")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # ── Logging ───────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")


settings = Settings()
