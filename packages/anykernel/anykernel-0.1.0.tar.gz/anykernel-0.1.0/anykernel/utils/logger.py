"""Friendly logging system for AnyKernel."""

import logging
import sys
from typing import Optional


class AnyKernelFormatter(logging.Formatter):
    """Custom formatter with colors and AnyKernel prefix."""

    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    PREFIX = "[AnyKernel]"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()

        if self.use_colors:
            color = self.COLORS.get(record.levelno, "")
            return f"{color}{self.PREFIX}{self.RESET} {message}"
        return f"{self.PREFIX} {message}"


class AnyKernelLogger:
    """Logger wrapper for AnyKernel with friendly output."""

    _instance: Optional["AnyKernelLogger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        """Set up the logger with custom formatting."""
        self._logger = logging.getLogger("anykernel")
        self._logger.setLevel(logging.INFO)

        # Remove existing handlers
        self._logger.handlers.clear()

        # Add custom handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(AnyKernelFormatter())
        self._logger.addHandler(handler)

        # Prevent propagation to root logger
        self._logger.propagate = False

    def debug(self, message: str):
        """Log debug message."""
        self._logger.debug(message)

    def info(self, message: str):
        """Log info message."""
        self._logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self._logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self._logger.error(message)

    def critical(self, message: str):
        """Log critical message."""
        self._logger.critical(message)

    def set_level(self, level: str):
        """Set logging level."""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        self._logger.setLevel(level_map.get(level.lower(), logging.INFO))


def get_logger() -> AnyKernelLogger:
    """Get the AnyKernel logger instance."""
    return AnyKernelLogger()


def set_log_level(level: str):
    """Set the global log level for AnyKernel.

    Args:
        level: One of "debug", "info", "warning", "error", "critical"
    """
    get_logger().set_level(level)
