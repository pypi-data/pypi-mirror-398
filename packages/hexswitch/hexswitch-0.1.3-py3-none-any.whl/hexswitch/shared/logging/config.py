"""Logging configuration for HexSwitch."""

from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import sys
from typing import Any, Dict, Optional


class LogFormat(str, Enum):
    """Supported log formats."""

    TEXT = "text"
    JSON = "json"


@dataclass
class LoggingConfig:
    """Configuration for logging setup.

    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: Log format (text or json).
        include_timestamp: Whether to include timestamp in logs.
        service_name: Service name to include in logs.
        logger_name: Root logger name (default: "hexswitch").
        stream: Output stream (default: sys.stderr).
        extra_fields: Additional fields to include in JSON logs.
    """

    level: str = "INFO"
    format: LogFormat = LogFormat.TEXT
    include_timestamp: bool = True
    service_name: Optional[str] = None
    logger_name: str = "hexswitch"
    stream: Any = field(default_factory=lambda: sys.stderr)
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {self.level}. Must be one of {valid_levels}"
            )


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(
        self,
        service_name: Optional[str] = None,
        include_timestamp: bool = True,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        """Initialize JSON formatter.

        Args:
            service_name: Service name to include in logs.
            include_timestamp: Whether to include timestamp.
            extra_fields: Additional fields to include in all log records.
        """
        super().__init__()
        self.service_name = service_name
        self.include_timestamp = include_timestamp
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            log_data["timestamp"] = self.formatTime(record, self.datefmt)

        if self.service_name:
            log_data["service"] = self.service_name

        # Add extra fields
        log_data.update(self.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra attributes from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logging."""

    def __init__(
        self,
        service_name: Optional[str] = None,
        include_timestamp: bool = True,
    ):
        """Initialize text formatter.

        Args:
            service_name: Service name to include in logs.
            include_timestamp: Whether to include timestamp.
        """
        if include_timestamp:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            fmt = "%(name)s - %(levelname)s - %(message)s"

        if service_name:
            fmt = f"[{service_name}] {fmt}"

        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text.

        Args:
            record: Log record to format.

        Returns:
            Text-formatted log string.
        """
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    format: LogFormat = LogFormat.TEXT,  # noqa: A002
    include_timestamp: bool = True,
    service_name: Optional[str] = None,
    logger_name: str = "hexswitch",
    stream: Any = None,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> None:
    """Set up logging configuration.

    This function configures the root logger and can be used both
    internally by HexSwitch and by external projects.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: Log format (text or json).
        include_timestamp: Whether to include timestamp in logs.
        service_name: Service name to include in logs.
        logger_name: Root logger name (default: "hexswitch").
        stream: Output stream (default: sys.stderr).
        extra_fields: Additional fields to include in JSON logs.

    Example:
        >>> setup_logging(level="DEBUG", format=LogFormat.JSON)
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    config = LoggingConfig(
        level=level,
        format=format,
        include_timestamp=include_timestamp,
        service_name=service_name,
        logger_name=logger_name,
        stream=stream or sys.stderr,
        extra_fields=extra_fields or {},
    )

    # Get root logger
    root_logger = logging.getLogger(config.logger_name)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Set log level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    numeric_level = level_map.get(config.level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Create handler
    handler = logging.StreamHandler(config.stream)
    handler.setLevel(numeric_level)

    # Create formatter based on format
    if config.format == LogFormat.JSON:
        formatter = JSONFormatter(
            service_name=config.service_name,
            include_timestamp=config.include_timestamp,
            extra_fields=config.extra_fields,
        )
    else:
        formatter = TextFormatter(
            service_name=config.service_name,
            include_timestamp=config.include_timestamp,
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Prevent propagation to root logger if using custom logger name
    if config.logger_name != "root":
        root_logger.propagate = False

