"""Port class - named connection point between adapters and handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Port:
    """Port represents a named connection point between adapters and handlers.

    In hexagonal architecture, ports are the boundaries of the application.
    This Port implementation supports n:m multiplexing (multiple adapters can
    write to the same port, multiple handlers can read from it).
    """
    name: str
    handlers: list[Callable] = field(default_factory=list)
    routing_strategy: 'RoutingStrategy | None' = None  # type: ignore

    def __post_init__(self):
        """Initialize default routing strategy if not provided."""
        if self.routing_strategy is None:
            from hexswitch.ports.strategies import FirstStrategy
            self.routing_strategy = FirstStrategy()

    def route(self, envelope) -> list:
        """Route envelope to handlers using the configured strategy.

        Args:
            envelope: Request envelope from adapter.

        Returns:
            List of response envelopes from handlers.

        Raises:
            PortError: If no handlers are registered.
        """
        if not self.handlers:
            from hexswitch.ports.exceptions import NoHandlersError
            raise NoHandlersError(f"Port '{self.name}' has no handlers")

        return self.routing_strategy.route(envelope, self.handlers)

    def add_handler(self, handler: Callable) -> None:
        """Register a handler to this port.

        Args:
            handler: Handler function (Envelope -> Envelope).
        """
        self.handlers.append(handler)
