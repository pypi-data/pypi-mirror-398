"""MCP (Model Context Protocol) inbound adapter implementation."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from threading import Thread
from typing import Any

from hexswitch.adapters.base import InboundAdapter
from hexswitch.adapters.exceptions import AdapterStartError, AdapterStopError, HandlerError
from hexswitch.handlers.loader import HandlerLoader
from hexswitch.ports import PortError, get_port_registry
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class McpRequestHandler(BaseHTTPRequestHandler):
    """MCP JSON-RPC request handler for HexSwitch routes."""

    def __init__(
        self,
        methods: list[dict[str, Any]],
        adapter: "McpAdapterServer",
        handler_loader: HandlerLoader | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize MCP request handler.

        Args:
            methods: List of method configurations.
            adapter: Reference to McpAdapterServer instance (for converter access).
            handler_loader: Handler loader instance (optional).
            *args: Additional arguments for BaseHTTPRequestHandler.
            **kwargs: Additional keyword arguments for BaseHTTPRequestHandler.
        """
        self.methods = methods
        self._adapter = adapter
        self._handler_loader = handler_loader
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use our logger instead of stderr."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def do_POST(self) -> None:
        """Handle POST requests (MCP uses POST for JSON-RPC)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            # Parse JSON-RPC request
            jsonrpc_request = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_jsonrpc_error(-32700, "Parse error", None, str(e))
            return

        # Validate JSON-RPC 2.0 format
        if not isinstance(jsonrpc_request, dict):
            self._send_jsonrpc_error(-32600, "Invalid Request", None, "Request must be an object")
            return

        if jsonrpc_request.get("jsonrpc") != "2.0":
            self._send_jsonrpc_error(-32600, "Invalid Request", None, "jsonrpc must be '2.0'")
            return

        method_name = jsonrpc_request.get("method")
        request_id = jsonrpc_request.get("id")
        params = jsonrpc_request.get("params", {})

        if not method_name:
            self._send_jsonrpc_error(-32600, "Invalid Request", request_id, "method is required")
            return

        # Find matching method handler
        method_config = None
        for m in self.methods:
            if m.get("method_name") == method_name:
                method_config = m
                break

        if not method_config:
            self._send_jsonrpc_error(-32601, "Method not found", request_id, f"Method '{method_name}' not found")
            return

        # Load handler or port using HandlerLoader
        try:
            # Use handler loader if available, otherwise fall back to old method
            if self._handler_loader:
                if "port" in method_config:
                    handler = self._handler_loader.resolve(method_config["port"])
                elif "handler" in method_config:
                    handler = self._handler_loader.resolve(method_config["handler"])
                else:
                    logger.error(f"Method '{method_name}' must have either 'handler' or 'port' specified")
                    self._send_jsonrpc_error(-32603, "Internal error", request_id, "Method configuration error")
                    return
            else:
                # Fallback to old method for backward compatibility
                if "port" in method_config:
                    handler = get_port_registry().get_handler(method_config["port"])
                elif "handler" in method_config:
                    handler_path = method_config["handler"]
                    if ":" not in handler_path:
                        raise HandlerError(f"Invalid handler path format: {handler_path}. Expected format: 'module.path:function_name'")
                    module_path, function_name = handler_path.rsplit(":", 1)
                    if not module_path or not function_name:
                        raise HandlerError(f"Invalid handler path format: {handler_path}. Module path and function name must not be empty.")
                    import importlib
                    module = importlib.import_module(module_path)
                    if not hasattr(module, function_name):
                        raise HandlerError(f"Module '{module_path}' does not have attribute '{function_name}'")
                    handler = getattr(module, function_name)
                    if not callable(handler):
                        raise HandlerError(f"'{function_name}' in module '{module_path}' is not callable")
                else:
                    logger.error(f"Method '{method_name}' must have either 'handler' or 'port' specified")
                    self._send_jsonrpc_error(-32603, "Internal error", request_id, "Method configuration error")
                    return
        except (HandlerError, PortError) as e:
            logger.error(f"Failed to load handler/port for method '{method_name}': {e}")
            self._send_jsonrpc_error(-32603, "Internal error", request_id, str(e))
            return

        # Convert MCP JSON-RPC Request → Envelope using converter
        # Convert headers to dict, handling both HTTPMessage objects and mocks
        if isinstance(self.headers, dict):
            headers = self.headers
        else:
            try:
                headers = dict(self.headers)
            except (TypeError, AttributeError):
                # Fallback for mock objects or other non-dict types
                headers = {}

        request_envelope = self._adapter.to_envelope(
            method=method_name,
            params=params,
            request_id=request_id,
            headers=headers,
        )

        # Call handler/port with Envelope
        try:
            response_envelope = handler(request_envelope)
        except Exception as e:
            logger.exception(f"Handler/Port raised exception for method '{method_name}': {e}")
            self._send_jsonrpc_error(-32603, "Internal error", request_id, str(e))
            return

        # Convert Envelope (Response) → MCP JSON-RPC Response using converter
        jsonrpc_response = self._adapter.from_envelope(response_envelope, request_id)
        self._send_jsonrpc_response(jsonrpc_response)

    def _send_jsonrpc_response(self, response: dict[str, Any]) -> None:
        """Send JSON-RPC response.

        Args:
            response: JSON-RPC response dictionary.
        """
        response_body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def _send_jsonrpc_error(self, code: int, message: str, request_id: Any, data: Any = None) -> None:
        """Send JSON-RPC error response.

        Args:
            code: JSON-RPC error code.
            message: Error message.
            request_id: Request ID (can be None for parse errors).
            data: Optional error data.
        """
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message,
            },
            "id": request_id,
        }
        if data is not None:
            error_response["error"]["data"] = data

        response_body = json.dumps(error_response).encode("utf-8")
        self.send_response(200)  # JSON-RPC always returns 200, errors are in the JSON
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)


class McpAdapterServer(InboundAdapter):
    """MCP inbound adapter for HexSwitch."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize MCP adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._running = False
        self.server: HTTPServer | None = None
        self.server_thread: Thread | None = None
        self.port = config.get("port", 3000)
        self.methods = config.get("methods", [])
        self._handler_loader: HandlerLoader | None = None

    def start(self) -> None:
        """Start the MCP server.

        Raises:
            AdapterStartError: If the server fails to start.
        """
        if self._running:
            logger.warning(f"MCP adapter '{self.name}' is already running")
            return

        try:
            # Create request handler factory
            def handler_factory(*args: Any, **kwargs: Any) -> McpRequestHandler:
                return McpRequestHandler(self.methods, self, self._handler_loader, *args, **kwargs)

            # Create and start server
            self.server = HTTPServer(("", self.port), handler_factory)
            self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self._running = True

            logger.info(f"MCP adapter '{self.name}' started on port {self.port}")
        except Exception as e:
            raise AdapterStartError(f"Failed to start MCP adapter '{self.name}': {e}") from e

    def stop(self) -> None:
        """Stop the MCP server.

        Raises:
            AdapterStopError: If the server fails to stop.
        """
        if not self._running:
            logger.warning(f"MCP adapter '{self.name}' is not running")
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=5.0)
            self._running = False
            logger.info(f"MCP adapter '{self.name}' stopped")
        except Exception as e:
            raise AdapterStopError(f"Failed to stop MCP adapter '{self.name}': {e}") from e

    def to_envelope(
        self,
        method: str,
        params: dict[str, Any],
        request_id: Any,
        headers: dict[str, str],
    ) -> Envelope:
        """Convert MCP JSON-RPC request to Envelope.

        Args:
            method: MCP method name.
            params: MCP method parameters.
            request_id: JSON-RPC request ID.
            headers: HTTP headers.

        Returns:
            Request envelope.
        """
        return Envelope(
            path=f"/{method}",
            method="POST",
            body=params,
            headers=headers,
            metadata={
                "mcp_method": method,
                "mcp_request_id": request_id,
                "jsonrpc": "2.0",
            },
        )

    def from_envelope(self, envelope: Envelope, request_id: Any) -> dict[str, Any]:
        """Convert Envelope response to MCP JSON-RPC response.

        Args:
            envelope: Response envelope.
            request_id: JSON-RPC request ID.

        Returns:
            JSON-RPC response dictionary.
        """
        if envelope.error_message:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": envelope.status_code or -32603,
                    "message": envelope.error_message,
                },
                "id": request_id,
            }

        return {
            "jsonrpc": "2.0",
            "result": envelope.data or {},
            "id": request_id,
        }

