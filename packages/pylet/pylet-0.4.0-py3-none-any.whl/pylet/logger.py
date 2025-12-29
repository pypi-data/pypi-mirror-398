"""
PyLet Logging - Configurable logging with deferred file handler creation.

Console logging is enabled by default. File logging must be explicitly
configured via configure_file_logging() to avoid creating log files
when the module is merely imported.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Create a custom logger named 'pylet'
logger = logging.getLogger("pylet")
logger.setLevel(logging.DEBUG)

# Only add console handler at import time (no file creation)
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.DEBUG)
_console_format = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
)
_console_handler.setFormatter(_console_format)
logger.addHandler(_console_handler)

# Track whether file logging has been configured
_file_handler: Optional[RotatingFileHandler] = None


def configure_file_logging(
    log_path: Optional[Path] = None,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 2,
) -> None:
    """
    Configure file logging for pylet.

    Args:
        log_path: Path to log file. Defaults to ~/.pylet/pylet.log
        level: Logging level for file handler (default INFO)
        max_bytes: Max size per log file before rotation (default 5MB)
        backup_count: Number of backup files to keep (default 2)
    """
    global _file_handler

    # Avoid duplicate handlers
    if _file_handler is not None:
        return

    # Default to ~/.pylet/pylet.log
    if log_path is None:
        from pylet import config
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        log_path = config.DATA_DIR / "pylet.log"
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    _file_handler = RotatingFileHandler(
        str(log_path), maxBytes=max_bytes, backupCount=backup_count
    )
    _file_handler.setLevel(level)

    file_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    _file_handler.setFormatter(file_format)

    logger.addHandler(_file_handler)


def set_console_level(level: int) -> None:
    """Set the console logging level."""
    _console_handler.setLevel(level)
