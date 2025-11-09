from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

env_path = Path(__file__).resolve().parent.parent.parent / '.env'

class Settings(BaseSettings):
    """Manages application settings using Pydantic."""
    # Use the modern Pydantic v2 syntax
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8", extra="ignore")

    # GCP Configuration
    GCP_PROJECT_ID: str
    GCP_REGION: str = "us-central1"
    GCP_SOURCE_BUCKET_NAME: str
    FIRESTORE_SERVICES_COLLECTION: str = "services"
    GEMINI_API_KEY: str
    GCP_SIGNER_SERVICE_ACCOUNT_EMAIL: Optional[str] = None
    # Default CORS origins for local development.
    # In production, this is overridden by the Cloud Run environment variable.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    API_V1_STR: str = "/api/v1"

settings = Settings()