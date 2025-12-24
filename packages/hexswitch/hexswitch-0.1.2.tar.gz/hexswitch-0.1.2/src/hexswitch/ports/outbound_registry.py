"""Outbound port registry for managing outbound ports and their factories."""

from __future__ import annotations

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

# Global registry instance
_global_outbound_registry: OutboundPortRegistry | None = None


def get_outbound_registry() -> OutboundPortRegistry:
    """Get global outbound port registry instance.

    Returns:
        Global OutboundPortRegistry instance
    """
    global _global_outbound_registry
    if _global_outbound_registry is None:
        _global_outbound_registry = OutboundPortRegistry()
    return _global_outbound_registry


class OutboundPort:
    """Represents an outbound port with a factory function."""

    def __init__(self, name: str, factory: Callable):
        """Initialize outbound port.

        Args:
            name: Port name
            factory: Factory function that creates envelopes (e.g., `lambda *args, **kwargs: Envelope(...)`)
        """
        self.name = name
        self.factory = factory


class OutboundPortRegistry:
    """Registry for managing outbound ports and their factories.

    Thread-safe registry that stores outbound ports with their factory functions.
    """

    def __init__(self):
        """Initialize outbound port registry."""
        self._ports: dict[str, OutboundPort] = {}
        self._lock = threading.Lock()

    def register_port(self, port_name: str, factory: Callable) -> None:
        """Register outbound port with factory.

        Args:
            port_name: Port name
            factory: Factory function that creates envelopes from args/kwargs
        """
        with self._lock:
            if port_name in self._ports:
                logger.warning(f"Outbound port '{port_name}' already registered, overwriting")
            self._ports[port_name] = OutboundPort(port_name, factory)
            logger.debug(f"Registered outbound port '{port_name}'")

    def get_port(self, port_name: str) -> OutboundPort | None:
        """Get outbound port by name.

        Args:
            port_name: Port name

        Returns:
            OutboundPort instance or None if not found
        """
        with self._lock:
            return self._ports.get(port_name)

    def list_ports(self) -> list[str]:
        """List all registered outbound port names.

        Returns:
            List of port names
        """
        with self._lock:
            return list(self._ports.keys())

    def remove_port(self, port_name: str) -> None:
        """Remove outbound port from registry.

        Args:
            port_name: Port name
        """
        with self._lock:
            self._ports.pop(port_name, None)
            logger.debug(f"Removed outbound port '{port_name}'")

    def clear(self) -> None:
        """Clear all outbound ports from registry."""
        with self._lock:
            self._ports.clear()

