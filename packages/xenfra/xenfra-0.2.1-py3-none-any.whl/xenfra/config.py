# src/xenfra/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str
    ENCRYPTION_KEY: str

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str
    GITHUB_WEBHOOK_SECRET: str

    DO_CLIENT_ID: str
    DO_CLIENT_SECRET: str
    DO_REDIRECT_URI: str

    # Frontend redirect for successful OAuth (e.g., /dashboard/connections)
    FRONTEND_OAUTH_REDIRECT_SUCCESS: str = "/dashboard/connections"

settings = Settings()
