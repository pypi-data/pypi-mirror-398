"""Logging module for HexSwitch.

This module provides a configurable logging system that can be used
both internally by HexSwitch and by external projects using the framework.

Example usage:
    from hexswitch.shared.logging import setup_logging, get_logger

    # Setup logging with default configuration
    setup_logging()

    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Application started")

    # Setup with custom configuration
    setup_logging(
        level="DEBUG",
        format="json",
        include_timestamp=True,
        service_name="my-service"
    )
"""

from hexswitch.shared.logging.config import (
    LogFormat,
    LoggingConfig,
    setup_logging,
)
from hexswitch.shared.logging.logger import get_logger

__all__ = [
    "LogFormat",
    "LoggingConfig",
    "get_logger",
    "setup_logging",
]

