"""Port exceptions."""


class PortError(Exception):
    """Base exception for port-related errors."""
    pass


class PortNotFoundError(PortError):
    """Raised when a port is not found in the registry."""
    pass


class NoHandlersError(PortError):
    """Raised when a port has no handlers registered."""
    pass
