"""Configuration management for PyAutokit scripts."""

import os
from pathlib import Path
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration management."""

    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    BACKUPS_DIR: Path = PROJECT_ROOT / "backups"

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FILE_ORG_SORT_BY: str = os.getenv("FILE_ORG_SORT_BY", "extension")
    FILE_ORG_CREATE_FOLDERS: bool = os.getenv(
        "FILE_ORG_CREATE_FOLDERS", "true"
    ).lower() == "true"

    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "10"))
    SCRAPER_RATE_LIMIT: float = float(os.getenv("SCRAPER_RATE_LIMIT", "1.0"))
    SCRAPER_USER_AGENT: str = os.getenv(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    EMAIL_SMTP_SERVER: str = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

    API_BASE_URL: str = os.getenv("API_BASE_URL", "")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    API_RETRIES: int = int(os.getenv("API_RETRIES", "3"))
    API_RETRY_DELAY: int = int(os.getenv("API_RETRY_DELAY", "2"))
    API_KEY: str = os.getenv("API_KEY", "")

    EGLD_PRICE_API: str = "https://api.coingecko.com/api/v3"
    BLOCKCHAIN_MONITOR_INTERVAL: int = int(
        os.getenv("BLOCKCHAIN_MONITOR_INTERVAL", "300")
    )

    BACKUP_COMPRESSION: str = os.getenv("BACKUP_COMPRESSION", "zip")
    BACKUP_KEEP_VERSIONS: int = int(os.getenv("BACKUP_KEEP_VERSIONS", "5"))

    @classmethod
    def create_directories(cls) -> None:
        """Create necessary project directories."""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.BACKUPS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


Config.create_directories()