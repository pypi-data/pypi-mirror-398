"""
Logging utilities for Investify services.

Usage:
    from investify_utils.logging import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)
"""

import logging
import os
from enum import IntEnum, auto
from logging.handlers import RotatingFileHandler

old_factory = logging.getLogRecordFactory()
default_logging_fmt = "%(asctime)s - %(origin)-30s - %(levelname)s - %(message)s"


class TextColor(IntEnum):
    """ANSI text colors for terminal output."""

    BLACK = 0
    RED = auto()
    GREEN = auto()
    YELLOW = auto()
    BLUE = auto()
    MAGENTA = auto()
    CYAN = auto()
    WHITE = auto()

    @staticmethod
    def colorize(text: str, color: "TextColor") -> str:
        """Wrap text with ANSI color codes."""
        return f"\033[0;{30 + color}m{text}\033[0m"


def record_factory(*args, **kwargs):
    """Custom log record factory that adds origin (filename:lineno)."""
    record = old_factory(*args, **kwargs)
    record.origin = f"{record.filename}:{record.lineno}"
    return record


def setup_logging(level=logging.INFO, logging_fmt=default_logging_fmt):
    """
    Configure logging with origin field (filename:lineno).

    Args:
        level: Logging level (default: INFO)
        logging_fmt: Log format string
    """
    logging.setLogRecordFactory(record_factory)
    logging.basicConfig(format=logging_fmt, level=level)


def setup_file_logging(
    filename: str,
    level=logging.INFO,
    max_megabytes: int = 1,
    backup_count: int = 3,
    logging_fmt: str = default_logging_fmt,
):
    """
    Configure rotating file logging.

    Args:
        filename: Log file path
        level: Logging level
        max_megabytes: Max file size before rotation
        backup_count: Number of backup files to keep
        logging_fmt: Log format string
    """
    filepath, _ = os.path.split(filename)
    if filepath and not os.path.isdir(filepath):
        os.makedirs(filepath)

    max_log_size = int(max_megabytes * 1024 * 1024)
    handler = RotatingFileHandler(filename=filename, maxBytes=max_log_size, backupCount=backup_count)
    logging.setLogRecordFactory(record_factory)
    logging.basicConfig(format=logging_fmt, level=level, handlers=[handler])
