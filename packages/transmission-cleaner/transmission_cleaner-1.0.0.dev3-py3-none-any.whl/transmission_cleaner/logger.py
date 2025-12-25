"""Logging configuration for transmission-cleaner.

Provides structured logging with configurable output levels and formats.
"""

import logging
import sys
from enum import Enum
from typing import TextIO


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    # Label prefixes for different log types
    LABELS = {
        "DEBUG": "[DEBUG]  ",
        "INFO": "[INFO]   ",
        "WARNING": "[WARN]   ",
        "ERROR": "[ERROR]  ",
        "CRITICAL": "[CRIT]   ",
    }

    def __init__(self, use_color: bool = True):
        """Initialize formatter.

        Args:
            use_color: Whether to use ANSI color codes
        """
        super().__init__()
        self.use_color = use_color and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors.

        Args:
            record: Log record to format

        Returns:
            Formatted log message
        """
        label = self.LABELS.get(record.levelname, f"[{record.levelname}] ")

        if self.use_color:
            color = self.COLORS.get(record.levelname, "")
            reset = self.COLORS["RESET"]
            label = f"{color}{label}{reset}"

        return f"{label}{record.getMessage()}"


class TransmissionLogger:
    """Logger wrapper with convenience methods for transmission-cleaner."""

    def __init__(self, name: str = "transmission-cleaner", level: str = "INFO"):
        """Initialize logger.

        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()

        # Console handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)

    def filter(self, message: str, **kwargs) -> None:
        """Log filter operation."""
        self.logger.info(f"[FILTER] {message}", **kwargs)

    def action(self, message: str, **kwargs) -> None:
        """Log action being taken."""
        self.logger.info(f"[ACTION] {message}", **kwargs)

    def skip(self, message: str, **kwargs) -> None:
        """Log skipped item."""
        self.logger.info(f"[SKIP]   {message}", **kwargs)

    def protected(self, message: str, **kwargs) -> None:
        """Log protected item."""
        self.logger.info(f"[PROTECTED] {message}", **kwargs)

    def cross_seed(self, message: str, **kwargs) -> None:
        """Log cross-seed detection."""
        self.logger.info(f"[CROSS-SEED] {message}", **kwargs)

    def prompt(self, message: str, **kwargs) -> None:
        """Log user prompt."""
        self.logger.info(f"[PROMPT] {message}", **kwargs)


def setup_logger(level: str = "INFO", quiet: bool = False) -> TransmissionLogger:
    """Setup and configure logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        quiet: If True, suppress all output except errors

    Returns:
        Configured logger instance
    """
    if quiet:
        level = "ERROR"

    return TransmissionLogger(level=level)


# Global logger instance
_logger: TransmissionLogger | None = None


def get_logger() -> TransmissionLogger:
    """Get or create global logger instance.

    Returns:
        Global logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def set_log_level(level: str) -> None:
    """Set global log level.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logger = get_logger()
    logger.logger.setLevel(getattr(logging, level.upper()))
