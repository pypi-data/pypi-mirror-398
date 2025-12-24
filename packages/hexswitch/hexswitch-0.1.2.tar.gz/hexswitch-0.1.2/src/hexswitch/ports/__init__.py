"""Ports system for hexagonal architecture.

Ports are named connection points between adapters and handlers.
This package provides the port registry, routing strategies, and decorators.
"""

# Import port decorator FIRST before port module to avoid name conflict
from hexswitch.ports.decorators import port as port_decorator
from hexswitch.ports.exceptions import NoHandlersError, PortError, PortNotFoundError
from hexswitch.ports.port import Port
from hexswitch.ports.registry import PortRegistry, get_port_registry, reset_port_registry
from hexswitch.ports.strategies import (
    BroadcastStrategy,
    FirstStrategy,
    RoundRobinStrategy,
    RoutingStrategy,
)

# Export port decorator as 'port' to avoid conflict with port module
port = port_decorator

__all__ = [
    # Core
    "Port",
    "PortRegistry",
    "get_port_registry",
    "reset_port_registry",

    # Strategies
    "RoutingStrategy",
    "FirstStrategy",
    "BroadcastStrategy",
    "RoundRobinStrategy",

    # Decorators
    "port",

    # Exceptions
    "PortError",
    "PortNotFoundError",
    "NoHandlersError",
]
