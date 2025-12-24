"""Adapter framework for HexSwitch."""

from hexswitch.adapters.base import InboundAdapter, OutboundAdapter
from hexswitch.adapters.exceptions import AdapterError, AdapterStartError, AdapterStopError

__all__ = [
    "InboundAdapter",
    "OutboundAdapter",
    "AdapterError",
    "AdapterStartError",
    "AdapterStopError",
]


