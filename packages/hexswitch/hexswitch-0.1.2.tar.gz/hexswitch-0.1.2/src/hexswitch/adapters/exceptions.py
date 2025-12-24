"""Adapter-specific exceptions."""


class AdapterError(Exception):
    """Base exception for adapter-related errors."""

    pass


class AdapterStartError(AdapterError):
    """Raised when an adapter fails to start."""

    pass


class AdapterStopError(AdapterError):
    """Raised when an adapter fails to stop."""

    pass


class AdapterConnectionError(AdapterError):
    """Raised when an adapter fails to connect to an external system."""

    pass


class HandlerError(AdapterError):
    """Raised when handler loading fails."""

    pass


