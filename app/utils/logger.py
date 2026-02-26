"""
Centralized logging configuration for the Traceability Tag Print API.

- Logs to both console and a rotating log file (logs/app.log).
- File rotation: 5 MB per file, keeps last 5 backups.
- Format: timestamp | level | logger name | message

Usage:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Server started")
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# ── Configuration ────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5

# Ensure the logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# ── Shared handlers (created once) ──────────────────────────────
_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
_file_handler.setLevel(LOG_LEVEL)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
_console_handler.setLevel(LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with file + console handlers attached.
    Calling this multiple times with the same name returns the same logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.propagate = False
    return logger
