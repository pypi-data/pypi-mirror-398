"""WebSocket inbound adapter implementation."""

import asyncio
import json
import logging
import socket
from threading import Thread
from typing import Any

import websockets
from websockets.server import WebSocketServerProtocol, serve

from hexswitch.adapters.base import InboundAdapter
from hexswitch.adapters.exceptions import AdapterStartError, AdapterStopError, HandlerError
from hexswitch.adapters.websocket._WebSocket_Envelope import WebSocketEnvelope
from hexswitch.handlers.loader import HandlerLoader
from hexswitch.ports import PortError, get_port_registry
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class WebSocketAdapterServer(InboundAdapter):
    """WebSocket inbound adapter for HexSwitch."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize WebSocket adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._running = False
        self._converter = WebSocketEnvelope()
        self.server: Any | None = None
        self.server_thread: Thread | None = None
        self.port = config.get("port", 8080)
        self.path = config.get("path", "/ws")
        self.routes = config.get("routes", [])
        self._handler_map: dict[str, Any] = {}
        self._connections: set[WebSocketServerProtocol] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._handler_loader: HandlerLoader | None = None

    def _load_handlers(self) -> None:
        """Load all handler functions for configured routes."""
        for route in self.routes:
            route_path = route.get("path", "")
            handler_path = route.get("handler", "")
            port_name = route.get("port", "")

            if not handler_path and not port_name:
                logger.warning(f"No handler or port specified for route '{route_path}', skipping")
                continue

            try:
                # Use handler loader if available, otherwise fall back to old method
                if self._handler_loader:
                    # Support both "handler:" and "port:" in config
                    if port_name:
                        handler = self._handler_loader.resolve(port_name)
                    elif handler_path:
                        handler = self._handler_loader.resolve(handler_path)
                    else:
                        continue
                    logger.debug(f"Loaded handler for route '{route_path}' via HandlerLoader")
                else:
                    # Fallback to old method for backward compatibility
                    if port_name:
                        handler = get_port_registry().get_handler(port_name)
                        logger.debug(f"Loaded port '{port_name}' for route '{route_path}'")
                    else:
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
                        logger.debug(f"Loaded handler for route '{route_path}': {handler_path}")
                self._handler_map[route_path] = handler
            except (HandlerError, PortError) as e:
                logger.error(f"Failed to load handler/port for route '{route_path}': {e}")
                raise

    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle a WebSocket connection.

        Args:
            websocket: WebSocket connection object.
            path: Request path.
        """
        self._connections.add(websocket)
        logger.info(f"WebSocket connection established: {path}")

        # Find matching route
        handler = None
        for route_path, route_handler in self._handler_map.items():
            if path == route_path or path.startswith(route_path):
                handler = route_handler
                break

        if not handler:
            logger.warning(f"No handler found for path: {path}")
            await websocket.close(code=4004, reason="No handler found")
            return

        try:
            # Call handler with connection info
            connection_data = {
                "path": path,
                "remote_address": websocket.remote_address,
                "websocket": websocket,
            }

            # Handler can be async or sync
            if asyncio.iscoroutinefunction(handler):
                await handler(connection_data)
            else:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, connection_data)

        except Exception as e:
            logger.exception(f"Error handling WebSocket connection on {path}: {e}")
            try:
                await websocket.close(code=1011, reason=str(e))
            except Exception:
                pass
        finally:
            self._connections.discard(websocket)
            logger.info(f"WebSocket connection closed: {path}")

    async def _handle_message(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle incoming WebSocket messages.

        Args:
            websocket: WebSocket connection object.
            path: Request path.
        """
        handler = None
        for route_path, route_handler in self._handler_map.items():
            if path == route_path or path.startswith(route_path):
                handler = route_handler
                break

        if not handler:
            return

        try:
            async for message in websocket:
                try:
                    # Convert WebSocket Message → Envelope using converter
                    remote_address = str(websocket.remote_address) if hasattr(websocket, "remote_address") else None
                    request_envelope = self.to_envelope(
                        message=message,
                        path=path,
                        remote_address=remote_address,
                        websocket_id=id(websocket),
                    )

                    # Call handler/port with Envelope
                    if asyncio.iscoroutinefunction(handler):
                        response_envelope = await handler(request_envelope)
                    else:
                        loop = asyncio.get_event_loop()
                        response_envelope = await loop.run_in_executor(None, handler, request_envelope)

                    # Convert Envelope (Response) → WebSocket Message using converter
                    response_message = self.from_envelope(response_envelope)
                    await websocket.send(response_message)

                except Exception as e:
                    logger.exception(f"Error processing WebSocket message on {path}: {e}")
                    try:
                        error_response = {"error": str(e)}
                        await websocket.send(json.dumps(error_response))
                    except Exception:
                        pass

        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"WebSocket connection closed normally: {path}")
        except Exception as e:
            logger.exception(f"Error in WebSocket message handler for {path}: {e}")

    async def _run_server(self) -> None:
        """Run the WebSocket server."""
        async with serve(
            self._handle_message, "0.0.0.0", self.port, path=self.path
        ) as server:
            self.server = server
            logger.info(f"WebSocket server started on port {self.port}, path: {self.path}")
            await asyncio.Future()  # Run forever

    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in a thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_server())
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
        finally:
            self._loop.close()

    def start(self) -> None:
        """Start the WebSocket server.

        Raises:
            AdapterStartError: If the server fails to start.
        """
        if self._running:
            logger.warning(f"WebSocket adapter '{self.name}' is already running")
            return

        try:
            # Load handlers
            self._load_handlers()

            # Check if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", self.port))
                s.close()

            # Start server in thread
            self.server_thread = Thread(target=self._run_event_loop, daemon=True)
            self.server_thread.start()

            # Give server time to start
            import time

            time.sleep(0.5)

            self._running = True
            logger.info(
                f"WebSocket adapter '{self.name}' started on port {self.port}, path: {self.path}"
            )
        except OSError as e:
            error_str = str(e)
            if "Address already in use" in error_str or "already in use" in error_str or "Only one usage" in error_str:
                raise AdapterStartError(
                    f"Port {self.port} is already in use for WebSocket adapter '{self.name}'"
                ) from e
            raise AdapterStartError(
                f"Failed to start WebSocket adapter '{self.name}': {e}"
            ) from e
        except Exception as e:
            raise AdapterStartError(f"Failed to start WebSocket adapter '{self.name}': {e}") from e

    def stop(self) -> None:
        """Stop the WebSocket server.

        Raises:
            AdapterStopError: If the server fails to stop.
        """
        if not self._running:
            logger.warning(f"WebSocket adapter '{self.name}' is not running")
            return

        try:
            # Close all connections
            if self._loop and self._loop.is_running():
                for conn in list(self._connections):
                    asyncio.run_coroutine_threadsafe(conn.close(), self._loop)

            # Stop server
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)

            if self.server_thread:
                self.server_thread.join(timeout=5.0)

            self._connections.clear()
            self._running = False
            logger.info(f"WebSocket adapter '{self.name}' stopped")
        except Exception as e:
            raise AdapterStopError(f"Failed to stop WebSocket adapter '{self.name}': {e}") from e

    def to_envelope(
        self,
        message: str | bytes,
        path: str,
        remote_address: str | None = None,
        websocket_id: int | None = None,
    ) -> Envelope:
        """Convert WebSocket message to Envelope.

        Args:
            message: WebSocket message.
            path: WebSocket path.
            remote_address: Remote address.
            websocket_id: WebSocket connection ID.

        Returns:
            Request envelope.
        """
        return self._converter.message_to_envelope(message, path, remote_address, websocket_id)

    def from_envelope(self, envelope: Envelope) -> str:
        """Convert Envelope response to WebSocket message.

        Args:
            envelope: Response envelope.

        Returns:
            WebSocket message as JSON string.
        """
        return self._converter.envelope_to_message(envelope)

