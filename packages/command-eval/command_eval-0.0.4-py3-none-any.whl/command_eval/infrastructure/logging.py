"""Logging infrastructure for command-eval.

Provides a configurable logger that can be enabled/disabled by library users.
"""

from __future__ import annotations

import logging
import sys
from enum import Enum
from typing import Callable


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class EvalLogger:
    """Configurable logger for command-eval library.

    Usage:
        ```python
        from command_eval.infrastructure.logging import get_logger, configure_logging

        # Enable verbose logging
        configure_logging(enabled=True, level=LogLevel.DEBUG)

        # Use logger
        logger = get_logger(__name__)
        logger.info("Processing test case", test_case_id="tc-001")
        ```
    """

    _instance: EvalLogger | None = None
    _enabled: bool = False
    _level: LogLevel = LogLevel.INFO
    _handler: logging.Handler | None = None
    _logger: logging.Logger | None = None

    def __new__(cls) -> EvalLogger:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self) -> None:
        """Set up the logger."""
        self._logger = logging.getLogger("command_eval")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

        # Remove existing handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

    def configure(
        self,
        enabled: bool = True,
        level: LogLevel = LogLevel.INFO,
        format_string: str | None = None,
    ) -> None:
        """Configure the logger.

        Args:
            enabled: Whether logging is enabled.
            level: The log level.
            format_string: Custom format string for log messages.
        """
        self._enabled = enabled
        self._level = level

        # Remove existing handler if any
        if self._handler is not None:
            self._logger.removeHandler(self._handler)
            self._handler = None

        if enabled:
            # Create console handler
            self._handler = logging.StreamHandler(sys.stderr)
            self._handler.setLevel(level.value)

            # Set format
            if format_string is None:
                format_string = (
                    "\033[36m[%(name)s]\033[0m "
                    "\033[33m%(levelname)s\033[0m "
                    "%(message)s"
                )

            formatter = logging.Formatter(format_string)
            self._handler.setFormatter(formatter)
            self._logger.addHandler(self._handler)

    @property
    def enabled(self) -> bool:
        """Check if logging is enabled."""
        return self._enabled

    def get_logger(self, name: str) -> logging.Logger:
        """Get a child logger.

        Args:
            name: The logger name (typically __name__).

        Returns:
            A logger instance.
        """
        return self._logger.getChild(name.split(".")[-1])


# Global logger instance
_eval_logger = EvalLogger()


def configure_logging(
    enabled: bool = True,
    level: LogLevel = LogLevel.INFO,
    format_string: str | None = None,
) -> None:
    """Configure the command-eval logging.

    Args:
        enabled: Whether logging is enabled.
        level: The log level.
        format_string: Custom format string for log messages.

    Example:
        ```python
        from command_eval.infrastructure.logging import configure_logging, LogLevel

        # Enable debug logging
        configure_logging(enabled=True, level=LogLevel.DEBUG)

        # Disable logging
        configure_logging(enabled=False)
        ```
    """
    _eval_logger.configure(enabled=enabled, level=level, format_string=format_string)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name.

    Args:
        name: The logger name (typically __name__).

    Returns:
        A logger instance.
    """
    return _eval_logger.get_logger(name)


def is_logging_enabled() -> bool:
    """Check if logging is enabled.

    Returns:
        True if logging is enabled.
    """
    return _eval_logger.enabled
