"""NATS outbound adapter implementation."""

import asyncio
import logging
import threading
from typing import Any

try:
    import nats
    from nats.aio.client import Client as NatsClient
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    NatsClient = None  # type: ignore

from hexswitch.adapters.base import OutboundAdapter
from hexswitch.adapters.exceptions import AdapterConnectionError
from hexswitch.adapters.nats._Nats_Envelope import NatsEnvelope
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class NatsAdapterClient(OutboundAdapter):
    """NATS outbound adapter for HexSwitch."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize NATS client adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._connected = False
        self._converter = NatsEnvelope()
        self.servers = config.get("servers", ["nats://localhost:4222"])
        if isinstance(self.servers, str):
            self.servers = [self.servers]
        self.timeout = config.get("timeout", 30.0)
        self._nc: NatsClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None

    def connect(self) -> None:
        """Connect to NATS server.

        Raises:
            AdapterConnectionError: If connection fails.
        """
        if self._connected:
            logger.warning(f"NATS client adapter '{self.name}' is already connected")
            return

        if not NATS_AVAILABLE:
            raise AdapterConnectionError(
                f"NATS client adapter '{self.name}' requires nats-py package. "
                "Install it with: pip install nats-py"
            )

        try:
            # Create event loop in new thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Connect to NATS
            self._loop.run_until_complete(self._async_connect())

            # Start event loop in background thread
            def run_loop():
                asyncio.set_event_loop(self._loop)
                self._loop.run_forever()

            self._loop_thread = threading.Thread(target=run_loop, daemon=True)
            self._loop_thread.start()
            self._connected = True

            logger.info(
                f"NATS client adapter '{self.name}' connected to {self.servers}"
            )
        except Exception as e:
            raise AdapterConnectionError(
                f"Failed to connect NATS client adapter '{self.name}': {e}"
            ) from e

    async def _async_connect(self) -> None:
        """Async connection logic."""
        self._nc = await nats.connect(servers=self.servers)

    def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if not self._connected:
            logger.warning(f"NATS client adapter '{self.name}' is not connected")
            return

        try:
            # Close connection
            if self._loop and self._loop.is_running():
                # Schedule async cleanup and wait for it to complete
                future = asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._loop)
                try:
                    future.result(timeout=5.0)
                except Exception as e:
                    logger.warning(f"Error waiting for async disconnect: {e}")

                # Stop event loop
                self._loop.call_soon_threadsafe(self._loop.stop)

                # Wait for thread to finish
                if self._loop_thread and self._loop_thread.is_alive():
                    self._loop_thread.join(timeout=5.0)

            self._connected = False
            logger.info(f"NATS client adapter '{self.name}' disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting NATS client adapter '{self.name}': {e}")

    async def _async_disconnect(self) -> None:
        """Async disconnection logic."""
        if self._nc:
            try:
                await self._nc.close()
            except Exception as e:
                logger.warning(f"Error closing NATS connection: {e}")
            self._nc = None

    def request(self, envelope: Envelope) -> Envelope:
        """Send envelope via NATS and return response.

        Args:
            envelope: Request envelope.

        Returns:
            Response envelope.

        Raises:
            AdapterConnectionError: If adapter is not connected or request fails.
        """
        if not self._connected or not self._nc:
            raise AdapterConnectionError(
                f"NATS client adapter '{self.name}' is not connected"
            )

        try:
            # Convert Envelope to NATS message
            subject = envelope.path  # Use envelope path as NATS subject
            message_data, headers = self._converter.envelope_to_message(envelope, subject=subject)

            # Use request/reply pattern if possible, otherwise just publish
            # For now, we'll use publish (fire-and-forget)
            # Request/reply can be added later if needed

            # Run async publish in event loop
            future = asyncio.run_coroutine_threadsafe(
                self._async_publish(subject, message_data, headers),
                self._loop
            )
            future.result(timeout=self.timeout)

            # For publish, return success envelope
            # For request/reply, we would wait for response here
            return Envelope.success({"status": "published", "subject": subject})

        except asyncio.TimeoutError as err:
            raise AdapterConnectionError(
                f"NATS request timeout after {self.timeout}s"
            ) from err
        except Exception as e:
            logger.exception(f"Error sending NATS message: {e}")
            return Envelope.error(500, f"Error sending NATS message: {str(e)}")

    async def _async_publish(self, subject: str, data: bytes, headers: dict[str, str]) -> None:
        """Async publish to NATS.

        Args:
            subject: NATS subject.
            data: Message data.
            headers: Message headers.
        """
        if not self._nc:
            raise AdapterConnectionError("NATS client not connected")
        await self._nc.publish(subject, data, headers=headers if headers else None)

    async def _async_request(
        self, subject: str, data: bytes, headers: dict[str, str], timeout: float
    ) -> Any:
        """Async request/reply to NATS.

        Args:
            subject: NATS subject.
            data: Message data.
            headers: Message headers.
            timeout: Request timeout.

        Returns:
            Response message.
        """
        if not self._nc:
            raise AdapterConnectionError("NATS client not connected")
        response = await self._nc.request(subject, data, timeout=timeout, headers=headers if headers else None)
        return response

