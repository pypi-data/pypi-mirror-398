"""WebSocket client outbound adapter implementation."""

import asyncio
import json
import logging
import threading
from typing import Any

import websockets

from hexswitch.adapters.base import OutboundAdapter
from hexswitch.adapters.exceptions import AdapterConnectionError
from hexswitch.adapters.websocket._WebSocket_Envelope import WebSocketEnvelope
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class WebSocketAdapterClient(OutboundAdapter):
    """WebSocket client outbound adapter for connecting to WebSocket servers."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize WebSocket client adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._connected = False
        self._converter = WebSocketEnvelope()
        self.url = config.get("url", "")
        self.timeout = config.get("timeout", 30)
        self.reconnect = config.get("reconnect", True)
        self.reconnect_interval = config.get("reconnect_interval", 5)
        self.websocket: Any = None  # websockets.asyncio.client.ClientConnection
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._receive_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue[Any] = asyncio.Queue()

    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in a thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"WebSocket client event loop error: {e}")
        finally:
            self._loop.close()

    async def _connect_async(self) -> None:
        """Connect to WebSocket server asynchronously."""
        try:
            self.websocket = await websockets.connect(
                self.url, timeout=self.timeout, ping_interval=None
            )
            logger.info(f"WebSocket client adapter '{self.name}' connected to {self.url}")
        except Exception as e:
            raise AdapterConnectionError(
                f"Failed to connect WebSocket client adapter '{self.name}' to {self.url}: {e}"
            ) from e

    async def _receive_messages(self) -> None:
        """Receive messages from WebSocket server."""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                try:
                    # Try to parse as JSON, fallback to raw message
                    try:
                        message_data = json.loads(message)
                    except (json.JSONDecodeError, TypeError):
                        message_data = {"raw": message}

                    await self._message_queue.put(message_data)
                except Exception as e:
                    logger.error(f"Error processing received message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {self.url}")
            if self.reconnect:
                await asyncio.sleep(self.reconnect_interval)
                try:
                    await self._connect_async()
                    if self.websocket:
                        self._receive_task = asyncio.create_task(self._receive_messages())
                except Exception as e:
                    logger.error(f"Failed to reconnect: {e}")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")

    def connect(self) -> None:
        """Connect to WebSocket server.

        Raises:
            AdapterConnectionError: If connection setup fails.
        """
        if self._connected:
            logger.warning(f"WebSocket client adapter '{self.name}' is already connected")
            return

        try:
            if not self.url:
                raise ValueError("url is required")

            # Start event loop in thread if not already running
            if not self._loop or not self._loop.is_running():
                self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
                self._loop_thread.start()

                # Wait for loop to start
                import time

                time.sleep(0.1)

            # Connect
            if self._loop:
                future = asyncio.run_coroutine_threadsafe(self._connect_async(), self._loop)
                future.result(timeout=self.timeout)

                # Start receiving messages
                future = asyncio.run_coroutine_threadsafe(
                    self._receive_messages(), self._loop
                )
                # Store the future, not the result
                self._receive_task = future
                # Wait briefly to ensure task started
                try:
                    future.result(timeout=0.1)
                except Exception:
                    pass  # Task is running, which is expected

            self._connected = True
            logger.info(f"WebSocket client adapter '{self.name}' connected to {self.url}")
        except Exception as e:
            raise AdapterConnectionError(
                f"Failed to connect WebSocket client adapter '{self.name}': {e}"
            ) from e

    def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if not self._connected:
            logger.warning(f"WebSocket client adapter '{self.name}' is not connected")
            return

        try:
            if self._receive_task:
                # Cancel the task if it's a Future from run_coroutine_threadsafe
                if hasattr(self._receive_task, 'cancel'):
                    self._receive_task.cancel()
                # If it's a Future, wait for cancellation to complete
                if hasattr(self._receive_task, 'result'):
                    try:
                        self._receive_task.result(timeout=1.0)
                    except Exception:
                        pass  # Ignore errors during cancellation

            if self._loop and self.websocket:
                future = asyncio.run_coroutine_threadsafe(self.websocket.close(), self._loop)
                try:
                    future.result(timeout=2)
                except Exception as e:
                    logger.error(f"Error closing WebSocket connection: {e}")

            self.websocket = None
            self._receive_task = None
            self._connected = False
            logger.info(f"WebSocket client adapter '{self.name}' disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket client adapter '{self.name}': {e}")

    def from_envelope(self, envelope: Envelope) -> str:
        """Convert Envelope request to WebSocket message.

        Args:
            envelope: Request envelope.

        Returns:
            WebSocket message as JSON string.
        """
        return self._converter.envelope_to_request(envelope)

    def to_envelope(
        self,
        message: str | bytes,
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert WebSocket response message to Envelope.

        Args:
            message: WebSocket message (string or bytes).
            original_envelope: Original request envelope.

        Returns:
            Response envelope.
        """
        return self._converter.message_to_envelope_response(message, original_envelope)

    def request(self, envelope: Envelope) -> Envelope:
        """Make WebSocket request using Envelope.

        Converts Envelope → WebSocket Message → WebSocket Message → Envelope.

        Args:
            envelope: Request envelope with path, body, etc.

        Returns:
            Response envelope.

        Raises:
            RuntimeError: If adapter is not connected.
        """
        if not self._connected or not self.websocket or not self._loop:
            raise RuntimeError(f"WebSocket client adapter '{self.name}' is not connected")

        # Convert Envelope → WebSocket Message using converter
        message = self.from_envelope(envelope)

        try:
            # Send message
            future = asyncio.run_coroutine_threadsafe(
                self._send_async(message), self._loop
            )
            future.result(timeout=self.timeout)

            # Wait for response (with timeout)
            import time
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    response_data = self._message_queue.get_nowait()
                    # Convert WebSocket Message → Envelope using converter
                    if isinstance(response_data, dict):
                        response_message = json.dumps(response_data)
                    else:
                        response_message = str(response_data)
                    return self.to_envelope(response_message, envelope)
                except asyncio.QueueEmpty:
                    time.sleep(0.1)
                    continue

            # Timeout
            return Envelope.error(504, "WebSocket request timeout")
        except Exception as e:
            logger.error(f"WebSocket request failed: {e}")
            return Envelope.error(500, str(e))

    async def _send_async(self, message: Any) -> None:
        """Send message asynchronously.

        Args:
            message: Message to send (dict, list, str, or bytes).
        """
        if not self.websocket:
            raise RuntimeError("WebSocket is not connected")

        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        elif isinstance(message, bytes):
            pass  # Send as-is
        else:
            message = str(message)

        await self.websocket.send(message)

    def send(self, message: Any) -> None:
        """Send message to WebSocket server.

        Args:
            message: Message to send (dict, list, str, or bytes).

        Raises:
            RuntimeError: If adapter is not connected.
        """
        if not self._connected or not self.websocket or not self._loop:
            raise RuntimeError(f"WebSocket client adapter '{self.name}' is not connected")

        try:
            future = asyncio.run_coroutine_threadsafe(self._send_async(message), self._loop)
            future.result(timeout=self.timeout)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    def receive(self, timeout: float | None = None) -> Any:
        """Receive message from WebSocket server.

        Args:
            timeout: Timeout in seconds (uses adapter timeout if not specified).

        Returns:
            Received message.

        Raises:
            RuntimeError: If adapter is not connected.
            TimeoutError: If no message received within timeout.
        """
        if not self._connected or not self._loop:
            raise RuntimeError(f"WebSocket client adapter '{self.name}' is not connected")

        receive_timeout = timeout if timeout is not None else self.timeout

        try:
            # Wait for message in queue
            future = asyncio.run_coroutine_threadsafe(
                asyncio.wait_for(self._message_queue.get(), timeout=receive_timeout), self._loop
            )
            return future.result(timeout=receive_timeout + 1)
        except asyncio.TimeoutError:
            raise TimeoutError(f"No message received within {receive_timeout} seconds")
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            raise

