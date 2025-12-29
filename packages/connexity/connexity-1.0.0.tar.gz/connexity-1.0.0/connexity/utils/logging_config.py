"""
Centralized logging configuration for the Connexity SDK.

This module provides a consistent logging interface with configurable log levels.

Usage:
    from connexity.utils.logging_config import get_logger, LogLevel

    # Get a logger with default INFO level
    logger = get_logger(__name__)

    # Get a logger with custom level
    logger = get_logger(__name__, level=LogLevel.DEBUG)

    # Configure global SDK log level
    configure_sdk_logging(level=LogLevel.WARNING)
"""

import logging
from enum import IntEnum

# SDK logger namespace - all SDK loggers will use this prefix
SDK_LOGGER_NAME = "connexity"

# Default format for SDK log messages
DEFAULT_FORMAT = "[Connexity SDK] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
COMPACT_FORMAT = "[Connexity SDK] %(name)s - %(levelname)s - %(message)s"


class LogLevel(IntEnum):
    """Log levels matching Python's logging module."""

    DEBUG = logging.DEBUG  # 10 - Detailed diagnostic information
    INFO = logging.INFO  # 20 - General operational information
    WARNING = logging.WARNING  # 30 - Warning messages for potential issues
    ERROR = logging.ERROR  # 40 - Error messages for failures
    CRITICAL = logging.CRITICAL  # 50 - Critical errors requiring immediate attention


# Global configuration state
_sdk_log_level: int = LogLevel.WARNING
_handler_configured: bool = False


def configure_sdk_logging(
    level: LogLevel = LogLevel.WARNING,
    format_string: str = COMPACT_FORMAT,
    handler: logging.Handler | None = None,
) -> None:
    """
    Configure global logging settings for the Connexity SDK.

    This function sets up the root SDK logger with the specified configuration.
    Call this once at application startup to customize SDK logging behavior.

    Args:
        level: The minimum log level to display. Default is WARNING to reduce noise.
        format_string: The format string for log messages.
        handler: Optional custom handler. If None, a StreamHandler is created.
    """
    global _sdk_log_level, _handler_configured

    _sdk_log_level = level

    # Get or create the SDK root logger
    sdk_logger = logging.getLogger(SDK_LOGGER_NAME)
    sdk_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    sdk_logger.handlers.clear()

    # Add handler
    if handler is None:
        handler = logging.StreamHandler()

    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    sdk_logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicate messages
    sdk_logger.propagate = False

    _handler_configured = True


def get_logger(
    name: str,
    level: LogLevel | None = None,
) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: The module name (typically __name__).
        level: Optional log level override for this specific logger.
               If None, uses the global SDK log level.

    Returns:
        A configured Logger instance.
    """
    global _handler_configured

    # Ensure we have a handler configured
    if not _handler_configured:
        configure_sdk_logging()

    # Create logger under SDK namespace
    if name.startswith(SDK_LOGGER_NAME):
        logger_name = name
    else:
        # Extract just the module name from full path
        module_name = name.split(".")[-1]
        logger_name = f"{SDK_LOGGER_NAME}.{module_name}"

    logger = logging.getLogger(logger_name)

    # Apply specific level if provided
    if level is not None:
        logger.setLevel(level)

    return logger


def set_sdk_log_level(level: LogLevel) -> None:
    """
    Change the global SDK log level at runtime.

    Args:
        level: The new log level to apply to all SDK loggers.
    """
    global _sdk_log_level
    _sdk_log_level = level

    sdk_logger = logging.getLogger(SDK_LOGGER_NAME)
    sdk_logger.setLevel(level)

    # Update all child loggers
    for handler in sdk_logger.handlers:
        handler.setLevel(level)
