"""Adapter registry for managing adapter instances and metadata."""

import threading
from typing import Any

from hexswitch.adapters.base import InboundAdapter, OutboundAdapter

# Adapter metadata mapping adapter names to import paths
ADAPTER_METADATA = {
    "http": {
        "inbound": "hexswitch.adapters.http.inbound_adapter:HttpAdapterServer",
        "outbound": "hexswitch.adapters.http:HttpAdapterClient",
        "direction": "both",
        "protocol": "http",
    },
    "grpc": {
        "inbound": "hexswitch.adapters.grpc:GrpcAdapterServer",
        "outbound": "hexswitch.adapters.grpc:GrpcAdapterClient",
        "direction": "both",
        "protocol": "grpc",
    },
    "websocket": {
        "inbound": "hexswitch.adapters.websocket:WebSocketAdapterServer",
        "outbound": "hexswitch.adapters.websocket:WebSocketAdapterClient",
        "direction": "both",
        "protocol": "websocket",
    },
    "nats": {
        "inbound": "hexswitch.adapters.nats:NatsAdapterServer",
        "outbound": "hexswitch.adapters.nats:NatsAdapterClient",
        "direction": "both",
        "protocol": "nats",
    },
    "mcp": {
        "inbound": "hexswitch.adapters.mcp:McpAdapterServer",
        "outbound": "hexswitch.adapters.mcp:McpAdapterClient",
        "direction": "both",
        "protocol": "mcp",
    },
}


class AdapterRegistry:
    """Registry for managing adapter instances and metadata.

    Thread-safe registry that stores adapter instances along with their metadata.
    """

    def __init__(self):
        """Initialize adapter registry."""
        self._adapters: dict[str, InboundAdapter | OutboundAdapter] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register(
        self, name: str, adapter: InboundAdapter | OutboundAdapter, metadata: dict[str, Any]
    ) -> None:
        """Register adapter instance with metadata.

        Args:
            name: Adapter name (e.g., "http", "grpc")
            adapter: Adapter instance
            metadata: Adapter metadata (direction, protocol, capabilities, etc.)
        """
        with self._lock:
            self._adapters[name] = adapter
            self._metadata[name] = metadata.copy()

    def get(self, name: str) -> InboundAdapter | OutboundAdapter | None:
        """Get adapter by name.

        Args:
            name: Adapter name

        Returns:
            Adapter instance or None if not found
        """
        with self._lock:
            return self._adapters.get(name)

    def get_metadata(self, name: str) -> dict[str, Any] | None:
        """Get adapter metadata by name.

        Args:
            name: Adapter name

        Returns:
            Adapter metadata or None if not found
        """
        with self._lock:
            return self._metadata.get(name)

    def list_inbound(self) -> list[str]:
        """List all inbound adapter names.

        Returns:
            List of adapter names that support inbound direction
        """
        with self._lock:
            return [
                name
                for name, metadata in self._metadata.items()
                if metadata.get("direction") in ("both", "inbound")
            ]

    def list_outbound(self) -> list[str]:
        """List all outbound adapter names.

        Returns:
            List of adapter names that support outbound direction
        """
        with self._lock:
            return [
                name
                for name, metadata in self._metadata.items()
                if metadata.get("direction") in ("both", "outbound")
            ]

    def list_all(self) -> list[str]:
        """List all registered adapter names.

        Returns:
            List of all adapter names
        """
        with self._lock:
            return list(self._adapters.keys())

    def remove(self, name: str) -> None:
        """Remove adapter from registry.

        Args:
            name: Adapter name
        """
        with self._lock:
            self._adapters.pop(name, None)
            self._metadata.pop(name, None)

    def clear(self) -> None:
        """Clear all adapters from registry."""
        with self._lock:
            self._adapters.clear()
            self._metadata.clear()

