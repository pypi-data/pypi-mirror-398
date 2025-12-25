import os
import platform
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()


def get_log_dir():
    """Get the platform-specific log directory"""
    if platform.system() == "Windows":
        # Windows: %LOCALAPPDATA%\CodeAudit23\logs
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            base_dir = Path(local_appdata) / "CodeAudit23"
        else:
            base_dir = Path.home() / "AppData" / "Local" / "CodeAudit23"
    elif platform.system() == "Darwin":
        # macOS: ~/Library/Logs/CodeAudit23
        base_dir = Path.home() / "Library" / "Logs" / "CodeAudit23"
    else:
        # Linux/Other: ~/.audit_scan/logs
        base_dir = Path.home() / ".audit_scan"

    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name):
    """
    Set up a logger with both file and console handlers.
    Logs are stored in a platform-specific application data directory.
    """
    import logging

    # Get platform-specific log directory
    log_dir = get_log_dir()

    # Initialize logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    # Formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter("%(levelname)-8s %(message)s")

    # File handler (rotating)
    log_file = log_dir / "audit_scanner.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Default logger instance
logger = setup_logger(__name__)
