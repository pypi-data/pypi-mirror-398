"""Routing strategies for ports."""

from abc import ABC, abstractmethod
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class RoutingStrategy(ABC):
    """Abstract base for routing strategies."""

    @abstractmethod
    def route(self, envelope, handlers: list[Callable]) -> list:
        """Route envelope to handlers.

        Args:
            envelope: Request envelope.
            handlers: List of handler functions.

        Returns:
            List of response envelopes.
        """
        pass


class FirstStrategy(RoutingStrategy):
    """Route to first handler only."""

    def route(self, envelope, handlers: list[Callable]) -> list:
        """Call only the first handler.

        Args:
            envelope: Request envelope.
            handlers: List of handler functions.

        Returns:
            Single-item list with response from first handler.
        """
        result = handlers[0](envelope)
        return [result]


class BroadcastStrategy(RoutingStrategy):
    """Route to all handlers, collect all results including errors."""

    def route(self, envelope, handlers: list[Callable]) -> list:
        """Call all handlers and collect results.

        Errors are caught and converted to error envelopes.

        Args:
            envelope: Request envelope.
            handlers: List of handler functions.

        Returns:
            List of response envelopes (one per handler).
        """
        # Import here to avoid circular dependency
        from hexswitch.shared.envelope import Envelope

        results = []
        for handler in handlers:
            try:
                result = handler(envelope)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed: {e}", exc_info=True)
                error_envelope = Envelope.error(500, f"Handler error: {str(e)}")
                results.append(error_envelope)
        return results


class RoundRobinStrategy(RoutingStrategy):
    """Route to handlers in round-robin fashion (for load balancing)."""

    def __init__(self):
        self._index = 0

    def route(self, envelope, handlers: list[Callable]) -> list:
        """Call next handler in round-robin order.

        Args:
            envelope: Request envelope.
            handlers: List of handler functions.

        Returns:
            Single-item list with response from selected handler.
        """
        handler = handlers[self._index % len(handlers)]
        self._index += 1
        result = handler(envelope)
        return [result]
