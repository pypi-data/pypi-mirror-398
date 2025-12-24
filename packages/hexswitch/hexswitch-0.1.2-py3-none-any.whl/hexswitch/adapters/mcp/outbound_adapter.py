"""MCP (Model Context Protocol) client outbound adapter implementation."""

import logging
from typing import Any

from hexswitch.adapters.base import OutboundAdapter
from hexswitch.adapters.exceptions import AdapterConnectionError
from hexswitch.adapters.http import HttpAdapterClient
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class McpAdapterClient(OutboundAdapter):
    """MCP client outbound adapter for communicating with MCP servers."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize MCP client adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._connected = False
        self.server_url = config.get("server_url", "")
        if not self.server_url:
            raise ValueError(f"MCP adapter '{name}' requires 'server_url' in config")

        # Create internal HTTP client adapter for JSON-RPC communication
        http_config = {
            "base_url": self.server_url,
            "timeout": config.get("timeout", 30),
            "headers": {
                "Content-Type": "application/json",
                **config.get("headers", {}),
            },
        }
        self._http_client = HttpAdapterClient(f"{name}_http", http_config)
        self._request_id = 0
        import threading

        self._request_id_lock = threading.Lock()

    def connect(self) -> None:
        """Connect to MCP server.

        Raises:
            AdapterConnectionError: If connection fails.
        """
        if self._connected:
            logger.warning(f"MCP client adapter '{self.name}' is already connected")
            return

        try:
            self._http_client.connect()
            # Test connection with initialize request
            self._send_request("initialize", {"protocolVersion": "2024-11-05"})
            self._connected = True
            logger.info(f"MCP client adapter '{self.name}' connected to {self.server_url}")
        except Exception as e:
            self._http_client.disconnect()
            raise AdapterConnectionError(
                f"Failed to connect MCP client adapter '{self.name}': {e}"
            ) from e

    def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if not self._connected:
            logger.warning(f"MCP client adapter '{self.name}' is not connected")
            return

        try:
            self._http_client.disconnect()
            self._connected = False
            logger.info(f"MCP client adapter '{self.name}' disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MCP client adapter '{self.name}': {e}")

    def _get_next_request_id(self) -> int:
        """Get next request ID.

        Returns:
            Next request ID.
        """
        with self._request_id_lock:
            self._request_id += 1
            return self._request_id

    def request(self, envelope: Envelope) -> Envelope:
        """Make MCP JSON-RPC request using Envelope.

        Converts Envelope → MCP JSON-RPC Request → MCP JSON-RPC Response → Envelope.

        Args:
            envelope: Request envelope with path (method name), body (params), etc.

        Returns:
            Response envelope.

        Raises:
            RuntimeError: If adapter is not connected.
        """
        if not self._http_client.is_connected():
            raise RuntimeError(f"MCP client adapter '{self.name}' HTTP client is not connected")

        # Convert Envelope → MCP JSON-RPC request using converter
        jsonrpc_request = self.from_envelope(envelope)

        # Create Envelope for HTTP request
        http_envelope = Envelope(
            path="",
            method="POST",
            body=jsonrpc_request,
            headers=envelope.headers,
            metadata={
                **envelope.metadata,
                "mcp_method": jsonrpc_request.get("method"),
                "mcp_request_id": jsonrpc_request.get("id"),
            },
        )

        try:
            # Call HTTP client adapter
            response_envelope = self._http_client.request(http_envelope)

            # Parse JSON-RPC response and convert to Envelope using converter
            if response_envelope.data:
                return self.to_envelope(response_envelope.data, envelope)
            else:
                return response_envelope
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            return Envelope.error(500, str(e))

    def from_envelope(self, envelope: Envelope) -> dict[str, Any]:
        """Convert Envelope request to MCP JSON-RPC request.

        Args:
            envelope: Request envelope.

        Returns:
            MCP JSON-RPC request dictionary.
        """
        # Extract method name from path
        method = envelope.path.strip("/") or envelope.metadata.get("method", "unknown")
        params = envelope.body or {}

        request_id = self._get_next_request_id()
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

    def to_envelope(
        self,
        jsonrpc_response: dict[str, Any],
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert MCP JSON-RPC response to Envelope.

        Args:
            jsonrpc_response: MCP JSON-RPC response.
            original_envelope: Original request envelope.

        Returns:
            Response envelope.
        """
        if "error" in jsonrpc_response:
            error = jsonrpc_response["error"]
            return Envelope.error(
                error.get("code", 500),
                f"MCP RPC error: {error.get('message', 'Unknown error')}",
            )

        return Envelope(
            path=original_envelope.path if original_envelope else "",
            method=original_envelope.method if original_envelope else None,
            status_code=200,
            data=jsonrpc_response.get("result", {}),
            metadata=original_envelope.metadata.copy() if original_envelope else {},
        )

    def _send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Legacy method for backwards compatibility.

        Args:
            method: RPC method name.
            params: RPC parameters.

        Returns:
            Response dictionary.

        Raises:
            RuntimeError: If HTTP client is not connected.
            ValueError: If response contains an error.
        """
        envelope = Envelope(
            path=f"/{method}",
            method="POST",
            body=params or {},
        )
        response_envelope = self.request(envelope)

        if response_envelope.error_message:
            raise ValueError(response_envelope.error_message)

        return response_envelope.data or {}

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call.
            arguments: Tool arguments.

        Returns:
            Tool result.
        """
        return self._send_request("tools/call", {"name": tool_name, "arguments": arguments or {}})

    def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools.

        Returns:
            List of available tools.
        """
        result = self._send_request("tools/list")
        return result.get("tools", [])

    def list_resources(self) -> list[dict[str, Any]]:
        """List available MCP resources.

        Returns:
            List of available resources.
        """
        result = self._send_request("resources/list")
        return result.get("resources", [])

    def get_resource(self, uri: str) -> dict[str, Any]:
        """Get an MCP resource.

        Args:
            uri: Resource URI.

        Returns:
            Resource data.
        """
        return self._send_request("resources/read", {"uri": uri})

