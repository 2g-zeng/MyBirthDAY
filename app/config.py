# app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """
    Global application settings.
    Values can be overridden by environment variables or a .env file.
    """
    # Base directory of the project
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Storage paths
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    VIDEO_DIR: Path = BASE_DIR / "storage" / "videos"

    # Database URL (SQLite file stored in storage/)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"

    class Config:
        env_file = ".env"


# This is the object imported in main.py
settings = Settings()
