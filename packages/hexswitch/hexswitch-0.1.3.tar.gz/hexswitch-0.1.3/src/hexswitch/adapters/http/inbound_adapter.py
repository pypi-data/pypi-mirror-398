"""HTTP inbound adapter implementation."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlparse

from hexswitch.adapters.base import InboundAdapter
from hexswitch.adapters.exceptions import AdapterStartError, AdapterStopError, HandlerError
from hexswitch.adapters.http._Http_Envelope import HttpEnvelope
from hexswitch.handlers.loader import HandlerLoader
from hexswitch.ports import PortError, get_port_registry
from hexswitch.shared.envelope import Envelope
from hexswitch.shared.helpers import parse_path_params

logger = logging.getLogger(__name__)


class HttpRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for HexSwitch routes."""

    def __init__(
        self,
        routes: list[dict[str, Any]],
        base_path: str,
        adapter: "HttpAdapterServer",
        handler_loader: HandlerLoader | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize HTTP request handler.

        Args:
            routes: List of route configurations.
            base_path: Base path prefix for all routes.
            adapter: Reference to HttpAdapterServer instance (for converter access).
            *args: Additional arguments for BaseHTTPRequestHandler.
            **kwargs: Additional keyword arguments for BaseHTTPRequestHandler.
        """
        self.routes = routes
        self.base_path = base_path.rstrip("/")
        self._adapter = adapter
        self._handler_loader = handler_loader
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use our logger instead of stderr."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def _handle_default_route(self, path: str, method: str) -> bool:
        """Handle default health and metrics routes.

        Args:
            path: Request path.
            method: HTTP method.

        Returns:
            True if route was handled, False otherwise.
        """
        if method.upper() != "GET":
            return False

        try:
            from hexswitch.handlers.health import (
                health_handler,
                liveness_handler,
                readiness_handler,
            )
            from hexswitch.handlers.metrics import metrics_handler
            from hexswitch.ports import PortError
            from hexswitch.shared.envelope import Envelope

            port_registry = get_port_registry()

            # Create a minimal envelope for the handler
            envelope = Envelope(path=path, body={})

            # Check health endpoints
            if path == "/health":
                try:
                    handler = port_registry.get_handler("__health__")
                except PortError:
                    handler = health_handler
                response = handler(envelope)
                self._send_response(response.status_code, response.data)
                return True

            if path == "/health/live":
                try:
                    handler = port_registry.get_handler("__live__")
                except PortError:
                    handler = liveness_handler
                response = handler(envelope)
                self._send_response(response.status_code, response.data)
                return True

            if path == "/health/ready":
                try:
                    handler = port_registry.get_handler("__ready__")
                except PortError:
                    handler = readiness_handler
                response = handler(envelope)
                self._send_response(response.status_code, response.data)
                return True

            # Metrics endpoint needs special handling
            if path == "/metrics":
                try:
                    handler = port_registry.get_handler("__metrics__")
                except PortError:
                    handler = metrics_handler
                response = handler(envelope)
                # Metrics returns Prometheus format in data["metrics"]
                metrics_text = response.data.get("metrics", "")
                # Send as plain text response
                response_body = metrics_text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
                return True

        except (ConnectionAbortedError, BrokenPipeError, OSError) as e:
            # Connection was closed by client - this is normal and not an error
            logger.debug(f"Connection closed by client during default route handling: {e}")
            return True
        except Exception as e:
            logger.exception(f"Error handling default route: {e}")
            try:
                self._send_response(500, {"error": "Internal Server Error", "message": str(e)})
            except (ConnectionAbortedError, BrokenPipeError, OSError):
                # Connection closed while sending error response - ignore
                pass
            return True

        return False

    def do_GET(self) -> None:
        """Handle GET requests."""
        self._handle_request("GET")

    def do_POST(self) -> None:
        """Handle POST requests."""
        self._handle_request("POST")

    def do_PUT(self) -> None:
        """Handle PUT requests."""
        self._handle_request("PUT")

    def do_DELETE(self) -> None:
        """Handle DELETE requests."""
        self._handle_request("DELETE")

    def do_PATCH(self) -> None:
        """Handle PATCH requests."""
        self._handle_request("PATCH")

    def _handle_request(self, method: str) -> None:
        """Handle HTTP request by routing to appropriate handler.

        Args:
            method: HTTP method.
        """
        parsed_url = urlparse(self.path)
        request_path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # Remove base_path prefix if present
        if self.base_path and request_path.startswith(self.base_path):
            request_path = request_path[len(self.base_path) :]

        # Check default routes first if enabled
        if self._adapter.enable_default_routes:
            if self._handle_default_route(request_path, method):
                return

        # Find matching route (support path parameters like /orders/:id)
        route = None
        import re

        for r in self.routes:
            if r["method"].upper() != method.upper():
                continue

            route_path = r["path"]
            # Exact match
            if route_path == request_path:
                route = r
                break

            # Check if route has path parameters (e.g., /orders/:id)
            if ":" in route_path:
                # Convert route pattern to regex for matching
                # Replace :param with regex group, but only for parameter names
                pattern = route_path
                # Find all :param patterns and replace them
                param_pattern = r":(\w+)"
                pattern = re.sub(param_pattern, r"([^/]+)", pattern)
                # Escape forward slashes for regex
                pattern = pattern.replace("/", r"\/")
                regex = re.compile(f"^{pattern}$")
                if regex.match(request_path):
                    route = r
                    break

        if not route:
            self._send_response(404, {"error": "Not Found"})
            return

        # Determine port name for pipeline routing
        port_name = None
        handler = None

        # Load handler or port using HandlerLoader (for fallback if pipeline not available)
        try:
            # Use handler loader if available, otherwise fall back to old method
            if self._handler_loader:
                # Support both "handler:" and "port:" in config
                if "port" in route:
                    port_name = route["port"]
                    handler = self._handler_loader.resolve(port_name)
                elif "handler" in route:
                    handler_path = route["handler"]
                    handler = self._handler_loader.resolve(handler_path)
                    # For handler paths, use handler path as port_name
                    port_name = handler_path
                else:
                    logger.error("Route must have either 'handler' or 'port' specified")
                    self._send_response(500, {"error": "Internal Server Error", "message": "Route configuration error"})
                    return
            else:
                # Fallback to old method for backward compatibility
                if "port" in route:
                    port_name = route["port"]
                    handler = get_port_registry().get_handler(port_name)
                elif "handler" in route:
                    handler_path = route["handler"]
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
                    port_name = handler_path
                else:
                    logger.error("Route must have either 'handler' or 'port' specified")
                    self._send_response(500, {"error": "Internal Server Error", "message": "Route configuration error"})
                    return
        except (HandlerError, PortError) as e:
            logger.error(f"Failed to load handler/port: {e}")
            self._send_response(500, {"error": "Internal Server Error", "message": str(e)})
            return

        # Convert HTTP Request → Envelope (Request) using converter
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # Extract path parameters
        path_params = parse_path_params(request_path, route["path"])

        # Parse query parameters (convert from parse_qs format)
        normalized_query_params: dict[str, Any] = {}
        for key, value in query_params.items():
            if isinstance(value, list):
                normalized_query_params[key] = value[0] if len(value) == 1 else value
            else:
                normalized_query_params[key] = value

        # Use converter to create Envelope
        request_envelope = self._adapter.to_envelope(
            method=method,
            path=request_path,
            headers=dict(self.headers),
            query_params=normalized_query_params,
            body=body,
            path_params=path_params,
        )

        # Set port_name in envelope metadata for pipeline routing
        if port_name:
            request_envelope.metadata["port_name"] = port_name

        # Try to use pipeline if runtime is available
        if hasattr(self._adapter, "_runtime") and self._adapter._runtime and port_name:
            try:
                import asyncio

                # Check if we're in an async context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're in an async context, but HTTP handler is sync
                        # Create a task or use run_coroutine_threadsafe
                        import concurrent.futures
                        future = concurrent.futures.Future()
                        asyncio.run_coroutine_threadsafe(
                            self._adapter._runtime.dispatch(request_envelope), loop
                        ).add_done_callback(lambda f: future.set_result(f.result()))
                        response_envelope = future.result(timeout=30)
                    else:
                        # No running loop, run async function
                        response_envelope = loop.run_until_complete(
                            self._adapter._runtime.dispatch(request_envelope)
                        )
                except RuntimeError:
                    # No event loop, create one
                    response_envelope = asyncio.run(self._adapter._runtime.dispatch(request_envelope))
            except Exception as e:
                logger.warning(f"Failed to use pipeline, falling back to direct handler call: {e}")
                # Fallback to direct handler call
                try:
                    response_envelope = handler(request_envelope)
                except Exception as handler_error:
                    logger.exception(f"Handler/Port raised exception: {handler_error}")
                    response_envelope = Envelope.error(500, "Internal Server Error")
        else:
            # No runtime available, use direct handler call
            try:
                response_envelope = handler(request_envelope)
            except Exception as e:
                logger.exception(f"Handler/Port raised exception: {e}")
                response_envelope = Envelope.error(500, "Internal Server Error")

        # Convert Envelope (Response) → HTTP Response using converter
        self._send_envelope_response(response_envelope)

    def _send_envelope_response(self, envelope: Envelope) -> None:
        """Send Envelope as HTTP response.

        Args:
            envelope: Response envelope.
        """
        # Use converter to convert Envelope to HTTP response
        status_code, data, headers = self._adapter.from_envelope(envelope)

        # Send response with headers
        response_body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))

        # Add headers from converter
        for header_name, header_value in headers.items():
            self.send_header(header_name, header_value)

        self.end_headers()
        self.wfile.write(response_body)

    def _send_response(self, status_code: int, data: dict[str, Any]) -> None:
        """Send JSON response.

        Args:
            status_code: HTTP status code.
            data: Response data dictionary.
        """
        try:
            response_body = json.dumps(data).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except (ConnectionAbortedError, BrokenPipeError, OSError):
            # Connection was closed by client - this is normal and not an error
            logger.debug("Connection closed by client while sending response")
            raise  # Re-raise to let caller handle it


class HttpAdapterServer(InboundAdapter):
    """HTTP inbound adapter for HexSwitch."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize HTTP adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._running = False
        self._converter = HttpEnvelope()
        self.server: HTTPServer | None = None
        self.server_thread: Thread | None = None
        self.port = config.get("port", 8000)
        self.base_path = config.get("base_path", "")
        self.routes = config.get("routes", [])
        self.enable_default_routes = config.get("enable_default_routes", True)
        self._handler_loader: HandlerLoader | None = None

    def start(self) -> None:
        """Start the HTTP server.

        Raises:
            AdapterStartError: If the server fails to start.
        """
        if self._running:
            logger.warning(f"HTTP adapter '{self.name}' is already running")
            return

        try:
            # Create request handler factory
            def handler_factory(*args: Any, **kwargs: Any) -> HttpRequestHandler:
                return HttpRequestHandler(self.routes, self.base_path, self, self._handler_loader, *args, **kwargs)

            # Create and start server
            self.server = HTTPServer(("", self.port), handler_factory)
            self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            # Give server time to start and verify it's listening
            import socket
            import time
            max_attempts = 200  # Increase attempts for slower systems
            self._running = True  # Mark as running, then verify
            server_ready = False
            for i in range(max_attempts):
                try:
                    # Check if server socket is bound and listening
                    if self.server.socket and self.server.socket.fileno() != -1:
                        # Try to connect to verify server is accepting connections
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(0.2)
                            result = s.connect_ex(("localhost", self.port))
                            if result == 0:
                                server_ready = True
                                logger.debug(f"HTTP adapter '{self.name}' verified listening on port {self.port} after {i*0.1}s")
                                break
                except Exception:
                    pass
                time.sleep(0.1)

            if not server_ready:
                logger.warning(f"HTTP adapter '{self.name}' may not be fully ready on port {self.port} after {max_attempts*0.1}s")
            else:
                # Give server a bit more time to be fully ready for HTTP requests
                time.sleep(0.2)

            logger.info(
                f"HTTP adapter '{self.name}' started on port {self.port} "
                f"with base_path '{self.base_path}'"
            )
        except Exception as e:
            raise AdapterStartError(f"Failed to start HTTP adapter '{self.name}': {e}") from e

    def stop(self) -> None:
        """Stop the HTTP server.

        Raises:
            AdapterStopError: If the server fails to stop.
        """
        if not self._running:
            logger.warning(f"HTTP adapter '{self.name}' is not running")
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=5.0)
            self._running = False
            logger.info(f"HTTP adapter '{self.name}' stopped")
        except Exception as e:
            raise AdapterStopError(f"Failed to stop HTTP adapter '{self.name}': {e}") from e

    def to_envelope(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        query_params: dict[str, Any],
        body: bytes | None,
        path_params: dict[str, str] | None = None,
    ) -> Envelope:
        """Convert HTTP request to Envelope.

        Args:
            method: HTTP method.
            path: Request path.
            headers: HTTP headers.
            query_params: Query parameters.
            body: Request body as bytes.
            path_params: Path parameters.

        Returns:
            Request envelope.
        """
        return self._converter.request_to_envelope(
            method=method,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body,
            path_params=path_params,
        )

    def from_envelope(self, envelope: Envelope) -> tuple[int, dict[str, Any], dict[str, str]]:
        """Convert Envelope response to HTTP response.

        Args:
            envelope: Response envelope.

        Returns:
            Tuple of (status_code, data, headers).
        """
        return self._converter.envelope_to_response(envelope)

