"""Logger utilities for HexSwitch."""

import logging


def get_logger(
    name: str,
    logger_name: str = "hexswitch",
    propagate: bool = True,
) -> logging.Logger:
    """Get a logger instance.

    This function provides a convenient way to get loggers that are
    properly configured to work with the HexSwitch logging system.

    Args:
        name: Logger name (typically __name__ of the calling module).
        logger_name: Root logger name (default: "hexswitch").
        propagate: Whether to propagate logs to parent logger.

    Returns:
        Configured logger instance.

    Example:
        >>> from hexswitch.shared.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    # Create logger name by combining root logger name with module name
    if logger_name == "root":
        full_name = name
    elif name and name.startswith(f"{logger_name}."):
        # If name already starts with logger_name, use it as-is to avoid duplication
        full_name = name
    elif name:
        full_name = f"{logger_name}.{name}"
    else:
        full_name = logger_name

    logger = logging.getLogger(full_name)
    logger.propagate = propagate

    return logger

