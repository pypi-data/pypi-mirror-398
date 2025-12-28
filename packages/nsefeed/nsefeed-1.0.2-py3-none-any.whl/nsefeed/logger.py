"""
Logging configuration for nsefeed library.

Provides minimalistic, professional logging with timestamps.
Log level can be controlled via NSEFEED_LOG_LEVEL environment variable.
File logging can be enabled via NSEFEED_LOG_FILE environment variable.

Example output:
    [2025-11-29 14:23:45] [INFO] Fetching RELIANCE history for period=1mo
    [2025-11-29 14:23:46] [DEBUG] Cache hit for RELIANCE on 2025-11-28
    [2025-11-29 14:23:47] [WARNING] Rate limit reached, sleeping for 1.0s
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from typing import Optional

from . import config as cfg

# Module-level logger instance
_logger: Optional[logging.Logger] = None


class NSEFeedFormatter(logging.Formatter):
    """
    Custom formatter for nsefeed logging.

    Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_colors: bool = True) -> None:
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        if self.use_colors:
            color = self.COLORS.get(level, self.COLORS["RESET"])
            reset = self.COLORS["RESET"]
            return f"[{timestamp}] [{color}{level}{reset}] {record.getMessage()}"
        return f"[{timestamp}] [{level}] {record.getMessage()}"


def get_logger(name: str = "nsefeed") -> logging.Logger:
    """
    Get or create the nsefeed logger.

    The logger is configured based on environment variables:
    - NSEFEED_LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - NSEFEED_LOG_FILE: Path to log file (optional)
    - NSEFEED_LOG_COLOR: Enable/disable colors (default: auto-detect)

    Args:
        name: Logger name (default: "nsefeed")

    Returns:
        Configured logging.Logger instance
    """
    global _logger

    if _logger is not None:
        return _logger

    # Create logger
    logger = logging.getLogger(name)

    # Get log level from config
    log_level_str = cfg.LOG_LEVEL
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Check color preference from config
    if cfg.LOG_COLOR is False:
        console_formatter = NSEFeedFormatter(use_colors=False)
    elif cfg.LOG_COLOR is True:
        console_formatter = NSEFeedFormatter(use_colors=True)
    else:  # "auto"
        console_formatter = NSEFeedFormatter(use_colors=True)  # Auto-detect

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    log_file = cfg.LOG_FILE
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(NSEFeedFormatter(use_colors=False))
            logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            logger.warning(f"Could not create log file '{log_file}': {e}")

    # Prevent propagation to root logger
    logger.propagate = False

    _logger = logger
    return logger


def set_log_level(level: str | int) -> None:
    """
    Set the log level for the nsefeed logger.

    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               or as int (logging.DEBUG, logging.INFO, etc.)
    """
    logger = get_logger()
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def enable_debug() -> None:
    """Enable debug logging for detailed output."""
    set_log_level(logging.DEBUG)


def disable_logging() -> None:
    """Disable all nsefeed logging."""
    logger = get_logger()
    logger.setLevel(logging.CRITICAL + 1)


def reset_logger() -> None:
    """Reset the logger to its initial state (useful for testing)."""
    global _logger
    if _logger is not None:
        _logger.handlers.clear()
        _logger = None


# Convenience functions for logging without explicit logger
def debug(msg: str, *args, **kwargs) -> None:
    """Log a debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Log an info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log a warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log an error message."""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """Log a critical message."""
    get_logger().critical(msg, *args, **kwargs)
