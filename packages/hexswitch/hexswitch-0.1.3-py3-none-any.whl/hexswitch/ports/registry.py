"""Port registry for managing ports and handlers."""

from __future__ import annotations

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class PortRegistry:
    """Registry for managing ports and their handlers.

    The registry maintains a mapping of port names to Port instances.
    Handlers register themselves on ports using the @port decorator.
    Adapters route envelopes through ports using the registry.
    """

    def __init__(self):
        self._ports: dict[str, 'Port'] = {}  # type: ignore
        self._lock = threading.Lock()

    def register_handler(
        self,
        port_name: str,
        handler: Callable,
        routing_strategy: 'RoutingStrategy | None' = None  # type: ignore
    ) -> None:
        """Register a handler on a port.

        If the port doesn't exist, it's created with the specified strategy.
        If it exists, the handler is added to the existing port.

        Args:
            port_name: Name of the port.
            handler: Handler function (Envelope -> Envelope).
            routing_strategy: Optional routing strategy (default: FirstStrategy).
        """
        from hexswitch.ports.port import Port
        from hexswitch.ports.strategies import FirstStrategy

        with self._lock:
            if port_name not in self._ports:
                strategy = routing_strategy or FirstStrategy()
                self._ports[port_name] = Port(
                    name=port_name,
                    handlers=[],
                    routing_strategy=strategy
                )
                logger.debug(f"Created port '{port_name}' with strategy {strategy.__class__.__name__}")

            self._ports[port_name].add_handler(handler)
            handler_count = len(self._ports[port_name].handlers)
            logger.debug(f"Registered handler '{handler.__name__}' on port '{port_name}' (total: {handler_count})")

    def route(self, port_name: str, envelope) -> list:
        """Route envelope through a port.

        Args:
            port_name: Name of the port.
            envelope: Request envelope.

        Returns:
            List of response envelopes from handlers.

        Raises:
            PortError: If port doesn't exist.
        """
        from hexswitch.ports.exceptions import PortNotFoundError

        with self._lock:
            if port_name not in self._ports:
                # Get available ports without acquiring lock again
                available = list(self._ports.keys())
                raise PortNotFoundError(
                    f"Port '{port_name}' not found. Available ports: {available}"
                )

            port = self._ports[port_name]

        # Route outside lock to allow concurrent handler execution
        return port.route(envelope)

    def get_port(self, port_name: str):
        """Get port by name.

        Args:
            port_name: Name of the port.

        Returns:
            Port instance.

        Raises:
            PortNotFoundError: If port doesn't exist.
        """
        from hexswitch.ports.exceptions import PortNotFoundError

        with self._lock:
            if port_name not in self._ports:
                raise PortNotFoundError(f"Port '{port_name}' not found")
            return self._ports[port_name]

    def get_handler(self, port_name: str):
        """Get first handler for a port (for backward compatibility).

        Args:
            port_name: Name of the port.

        Returns:
            First handler function.

        Raises:
            PortNotFoundError: If port doesn't exist.
            NoHandlersError: If port has no handlers.
        """
        from hexswitch.ports.exceptions import NoHandlersError, PortNotFoundError

        with self._lock:
            if port_name not in self._ports:
                raise PortNotFoundError(f"Port '{port_name}' not found")

            port = self._ports[port_name]
            if not port.handlers:
                raise NoHandlersError(f"Port '{port_name}' has no handlers")
            return port.handlers[0]

    def has_port(self, port_name: str) -> bool:
        """Check if port exists.

        Args:
            port_name: Name of the port.

        Returns:
            True if port exists, False otherwise.
        """
        with self._lock:
            return port_name in self._ports

    def list_ports(self) -> list[str]:
        """List all registered port names.

        Returns:
            List of port names.
        """
        with self._lock:
            return list(self._ports.keys())

    def set_routing_strategy(self, port_name: str, strategy) -> None:
        """Update routing strategy for a port.

        Args:
            port_name: Name of the port.
            strategy: New routing strategy.

        Raises:
            PortNotFoundError: If port doesn't exist.
        """
        from hexswitch.ports.exceptions import PortNotFoundError

        with self._lock:
            if port_name not in self._ports:
                raise PortNotFoundError(f"Port '{port_name}' not found")
            self._ports[port_name].routing_strategy = strategy
            logger.info(f"Updated routing strategy for port '{port_name}' to {strategy.__class__.__name__}")


# Global registry instance
_global_registry: PortRegistry | None = None
_registry_lock = threading.Lock()


def get_port_registry() -> PortRegistry:
    """Get or create the global port registry.

    Returns:
        Global PortRegistry instance.
    """
    global _global_registry
    with _registry_lock:
        if _global_registry is None:
            _global_registry = PortRegistry()
        return _global_registry


def reset_port_registry() -> None:
    """Reset the global port registry (useful for testing)."""
    global _global_registry
    with _registry_lock:
        _global_registry = None
