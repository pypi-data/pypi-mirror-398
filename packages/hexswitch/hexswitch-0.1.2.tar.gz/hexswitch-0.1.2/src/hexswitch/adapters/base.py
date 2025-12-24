"""Base classes for adapters."""

from abc import ABC, abstractmethod
from typing import Any


class InboundAdapter(ABC):
    """Base class for inbound adapters (receive requests from external systems)."""

    name: str
    config: dict[str, Any]

    @abstractmethod
    def start(self) -> None:
        """Start the adapter (e.g., start HTTP server)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the adapter gracefully."""
        pass

    def is_running(self) -> bool:
        """Check if adapter is running.

        Returns:
            True if adapter is running, False otherwise.
        """
        return getattr(self, "_running", False)


class OutboundAdapter(ABC):
    """Base class for outbound adapters (send requests to external systems)."""

    name: str
    config: dict[str, Any]

    @abstractmethod
    def connect(self) -> None:
        """Connect to external system."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from external system gracefully."""
        pass

    @abstractmethod
    def request(self, envelope):
        """Send request and get response."""
        pass

    def is_connected(self) -> bool:
        """Check if adapter is connected.

        Returns:
            True if adapter is connected, False otherwise.
        """
        return getattr(self, "_connected", False)

