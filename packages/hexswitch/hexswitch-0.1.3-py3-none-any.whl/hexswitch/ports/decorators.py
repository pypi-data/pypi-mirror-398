"""Port decorator for registering handlers."""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def port(
    name: str,
    routing: 'RoutingStrategy | None' = None  # type: ignore
) -> Callable:
    """Decorator to register a handler function on a port.

    Args:
        name: Port name.
        routing: Optional routing strategy (default: FirstStrategy).

    Returns:
        Decorator function.

    Example:
        >>> from hexswitch.ports import port
        >>> from hexswitch.shared.envelope import Envelope
        >>>
        >>> @port(name="create_order")
        >>> def create_order_handler(envelope: Envelope) -> Envelope:
        >>>     # Handler implementation
        >>>     return Envelope.success({"order_id": "123"})
        >>>
        >>> @port(name="log_events", routing=BroadcastStrategy())
        >>> def audit_logger(envelope: Envelope) -> Envelope:
        >>>     # Log to audit system
        >>>     return envelope
    """
    from hexswitch.ports.registry import get_port_registry

    registry = get_port_registry()

    def decorator(func: Callable) -> Callable:
        """Register function as handler on port."""

        # Preserve original function metadata
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Store port metadata on function
        wrapper._port_name = name  # type: ignore[attr-defined]
        wrapper._routing_strategy = routing  # type: ignore[attr-defined]

        # Register handler on port
        registry.register_handler(name, wrapper, routing)
        logger.debug(f"Decorated handler '{func.__name__}' registered on port '{name}'")

        return wrapper

    return decorator


def outbound_port(name: str) -> Callable:
    """Decorator for outbound ports.

    Registers a factory function that creates envelopes for outbound communication.

    Args:
        name: Port name

    Returns:
        Decorator function

    Example:
        >>> from hexswitch.ports import outbound_port
        >>> from hexswitch.shared.envelope import Envelope
        >>>
        >>> @outbound_port(name="external_api")
        >>> def create_external_api_envelope(order_id: str, amount: float) -> Envelope:
        >>>     return Envelope(
        >>>         path="/api/orders",
        >>>         method="POST",
        >>>         body={"id": order_id, "amount": amount}
        >>>     )
    """
    from hexswitch.ports.outbound_registry import get_outbound_registry

    def decorator(func: Callable) -> Callable:
        """Register function as outbound port factory."""

        # Preserve original function metadata
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Register in OutboundPortRegistry
        registry = get_outbound_registry()
        registry.register_port(name, wrapper)
        logger.debug(f"Decorated outbound port factory '{func.__name__}' registered on port '{name}'")

        return wrapper

    return decorator
