"""Route registry for inbound and outbound route matching."""

from dataclasses import dataclass
import logging
import threading
from typing import Any

from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


@dataclass
class OutboundTarget:
    """Represents an outbound target (adapter + config)."""

    adapter_name: str
    config: dict[str, Any]
    load_balancing: str = "first"  # first, round_robin, failover

    def __post_init__(self):
        """Validate load balancing strategy."""
        valid_strategies = ["first", "round_robin", "failover"]
        if self.load_balancing not in valid_strategies:
            raise ValueError(
                f"Invalid load balancing strategy: {self.load_balancing}. "
                f"Must be one of: {valid_strategies}"
            )


class OutboundRouteRegistry:
    """Registry for outbound route matching and target selection.

    Thread-safe registry that stores outbound routes (port_name → targets).
    """

    def __init__(self):
        """Initialize outbound route registry."""
        self._routes: dict[str, list[OutboundTarget]] = {}
        self._lock = threading.Lock()
        self._round_robin_counters: dict[str, int] = {}  # For round-robin load balancing

    def register_route(self, port_name: str, targets: list[OutboundTarget]) -> None:
        """Register outbound route.

        Args:
            port_name: Port name
            targets: List of outbound targets
        """
        with self._lock:
            self._routes[port_name] = targets.copy()
            self._round_robin_counters[port_name] = 0
            logger.debug(f"Registered outbound route for port '{port_name}' with {len(targets)} targets")

    def match_route(self, port_name: str) -> list[OutboundTarget] | None:
        """Match route and return targets.

        Args:
            port_name: Port name

        Returns:
            List of targets or None if route not found
        """
        with self._lock:
            return self._routes.get(port_name)

    def select_target(self, port_name: str, envelope: Envelope) -> OutboundTarget:
        """Select target based on load balancing strategy.

        Args:
            port_name: Port name
            envelope: Envelope (for potential routing decisions)

        Returns:
            Selected target

        Raises:
            ValueError: If no targets found or invalid strategy
        """
        targets = self.match_route(port_name)
        if not targets:
            raise ValueError(f"No targets found for port '{port_name}'")

        if len(targets) == 1:
            return targets[0]

        # Get load balancing strategy from first target (all should have same strategy)
        strategy = targets[0].load_balancing

        with self._lock:
            if strategy == "first":
                return targets[0]
            elif strategy == "round_robin":
                counter = self._round_robin_counters.get(port_name, 0)
                target = targets[counter % len(targets)]
                self._round_robin_counters[port_name] = (counter + 1) % len(targets)
                return target
            elif strategy == "failover":
                # For failover, always return first target (failover logic handled elsewhere)
                return targets[0]
            else:
                raise ValueError(f"Unknown load balancing strategy: {strategy}")

    def list_routes(self) -> list[str]:
        """List all registered route port names.

        Returns:
            List of port names
        """
        with self._lock:
            return list(self._routes.keys())

    def remove_route(self, port_name: str) -> None:
        """Remove route from registry.

        Args:
            port_name: Port name
        """
        with self._lock:
            self._routes.pop(port_name, None)
            self._round_robin_counters.pop(port_name, None)
            logger.debug(f"Removed outbound route for port '{port_name}'")

    def clear(self) -> None:
        """Clear all routes from registry."""
        with self._lock:
            self._routes.clear()
            self._round_robin_counters.clear()

