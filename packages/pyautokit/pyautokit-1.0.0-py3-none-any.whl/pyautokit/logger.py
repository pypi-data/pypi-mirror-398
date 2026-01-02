"""Centralized logging configuration."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from .config import Config


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO"
) -> logging.Logger:
    """Setup logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(Config.LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is None:
        log_file = Config.LOGS_DIR / f"{name}.log"
    else:
        log_file = Path(log_file)

    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger