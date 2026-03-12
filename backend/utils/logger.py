"""
Structured logging setup for the application.
Provides consistent log formatting across all modules.
"""

import logging
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Root logger instance
    """
    root_logger = logging.getLogger("ai_ops")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid adding duplicate handlers
    if root_logger.handlers:
        return root_logger

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-18s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: Logger name (typically module name like 'agent.cleaning')

    Returns:
        Logger instance
    """
    return logging.getLogger(f"ai_ops.{name}")
