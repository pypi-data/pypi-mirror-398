"""NATS inbound adapter implementation."""

import asyncio
import importlib
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

from hexswitch.adapters.base import InboundAdapter
from hexswitch.adapters.exceptions import AdapterStartError, AdapterStopError, HandlerError
from hexswitch.adapters.nats._Nats_Envelope import NatsEnvelope
from hexswitch.ports import PortError, get_port_registry

logger = logging.getLogger(__name__)


class NatsAdapterServer(InboundAdapter):
    """NATS inbound adapter for HexSwitch."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize NATS adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._running = False
        self._converter = NatsEnvelope()
        self.servers = config.get("servers", ["nats://localhost:4222"])
        if isinstance(self.servers, str):
            self.servers = [self.servers]
        self.subjects = config.get("subjects", [])
        self.queue_group = config.get("queue_group")
        self._nc: NatsClient | None = None
        self._subscriptions: list[Any] = []
        self._handler_map: dict[str, Any] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server_thread: threading.Thread | None = None
        self._handler_loader = None  # Will be set by runtime if available

    def _load_handlers(self) -> None:
        """Load all handler functions for configured subjects."""
        port_registry = get_port_registry()

        for subject_config in self.subjects:
            subject = subject_config.get("subject", "")
            handler_path = subject_config.get("handler", "")
            port_name = subject_config.get("port", "")

            if not handler_path and not port_name:
                logger.warning(f"No handler or port specified for subject '{subject}', skipping")
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
                    logger.debug(f"Loaded handler for subject '{subject}' via HandlerLoader")
                else:
                    # Fallback to old method for backward compatibility
                    if port_name:
                        handler = port_registry.get_handler(port_name)
                        logger.debug(f"Loaded port '{port_name}' for subject '{subject}'")
                    else:
                        if ":" not in handler_path:
                            raise HandlerError(
                                f"Invalid handler path format: {handler_path}. "
                                "Expected format: 'module.path:function_name'"
                            )
                        module_path, function_name = handler_path.rsplit(":", 1)
                        if not module_path or not function_name:
                            raise HandlerError(
                                f"Invalid handler path format: {handler_path}. "
                                "Module path and function name must not be empty."
                            )
                        module = importlib.import_module(module_path)
                        if not hasattr(module, function_name):
                            raise HandlerError(
                                f"Module '{module_path}' does not have attribute '{function_name}'"
                            )
                        handler = getattr(module, function_name)
                        if not callable(handler):
                            raise HandlerError(
                                f"'{function_name}' in module '{module_path}' is not callable"
                            )
                        logger.debug(f"Loaded handler for subject '{subject}': {handler_path}")
                self._handler_map[subject] = handler
            except (HandlerError, PortError) as e:
                logger.error(f"Failed to load handler/port for subject '{subject}': {e}")
                raise

    async def _message_handler(self, msg: Any) -> None:
        """Handle incoming NATS message.

        Args:
            msg: NATS message object.
        """
        try:
            subject = msg.subject
            reply_to = msg.reply

            # Find handler for this subject
            handler = self._handler_map.get(subject)
            if not handler:
                logger.warning(f"No handler found for subject: {subject}")
                return

            # Convert NATS message to Envelope
            headers = {}
            if hasattr(msg, "headers") and msg.headers:
                headers = dict(msg.headers.items())

            request_envelope = self._converter.message_to_envelope(
                subject=subject,
                data=msg.data,
                headers=headers,
                reply_to=reply_to,
            )

            # Call handler (sync or async)
            if asyncio.iscoroutinefunction(handler):
                response_envelope = await handler(request_envelope)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                response_envelope = await loop.run_in_executor(None, handler, request_envelope)

            # If reply_to is set, send response (request/reply pattern)
            if reply_to and response_envelope:
                message_data, response_headers = self._converter.envelope_to_message(
                    response_envelope, subject=reply_to
                )
                await self._nc.publish(reply_to, message_data, headers=response_headers)

        except Exception as e:
            logger.exception(f"Error processing NATS message on subject '{msg.subject}': {e}")

    def start(self) -> None:
        """Start the NATS adapter.

        Raises:
            AdapterStartError: If the adapter fails to start.
        """
        if self._running:
            logger.warning(f"NATS adapter '{self.name}' is already running")
            return

        if not NATS_AVAILABLE:
            raise AdapterStartError(
                f"NATS adapter '{self.name}' requires nats-py package. "
                "Install it with: pip install nats-py"
            )

        try:
            # Load handlers
            self._load_handlers()

            # Create event loop in new thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Run async setup in the event loop
            self._loop.run_until_complete(self._async_start())

            # Start event loop in background thread
            def run_loop():
                asyncio.set_event_loop(self._loop)
                self._loop.run_forever()

            self._server_thread = threading.Thread(target=run_loop, daemon=True)
            self._server_thread.start()
            self._running = True

            logger.info(
                f"NATS adapter '{self.name}' started, connected to {self.servers}, "
                f"subscribed to {len(self.subjects)} subjects"
            )
        except Exception as e:
            raise AdapterStartError(f"Failed to start NATS adapter '{self.name}': {e}") from e

    async def _async_start(self) -> None:
        """Async startup logic."""
        # Connect to NATS
        self._nc = await nats.connect(servers=self.servers)

        # Subscribe to all configured subjects
        for subject_config in self.subjects:
            subject = subject_config.get("subject", "")
            if not subject:
                continue

            # Subscribe with optional queue group
            if self.queue_group:
                sub = await self._nc.subscribe(
                    subject,
                    queue=self.queue_group,
                    cb=self._message_handler,
                )
            else:
                sub = await self._nc.subscribe(
                    subject,
                    cb=self._message_handler,
                )

            self._subscriptions.append(sub)
            logger.debug(f"Subscribed to NATS subject: {subject} (queue_group: {self.queue_group})")

    def stop(self) -> None:
        """Stop the NATS adapter.

        Raises:
            AdapterStopError: If the adapter fails to stop.
        """
        if not self._running:
            logger.warning(f"NATS adapter '{self.name}' is not running")
            return

        try:
            # Stop subscriptions and close connection
            if self._loop and self._loop.is_running():
                # Schedule async cleanup and wait for it to complete
                future = asyncio.run_coroutine_threadsafe(self._async_stop(), self._loop)
                try:
                    future.result(timeout=5.0)
                except Exception as e:
                    logger.warning(f"Error waiting for async stop: {e}")

                # Stop event loop
                self._loop.call_soon_threadsafe(self._loop.stop)

                # Wait for thread to finish
                if self._server_thread and self._server_thread.is_alive():
                    self._server_thread.join(timeout=5.0)

            self._running = False
            logger.info(f"NATS adapter '{self.name}' stopped")
        except Exception as e:
            raise AdapterStopError(f"Failed to stop NATS adapter '{self.name}': {e}") from e

    async def _async_stop(self) -> None:
        """Async shutdown logic."""
        # Unsubscribe from all subjects
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception as e:
                logger.warning(f"Error unsubscribing: {e}")

        # Close NATS connection
        if self._nc:
            try:
                await self._nc.close()
            except Exception as e:
                logger.warning(f"Error closing NATS connection: {e}")

        self._subscriptions.clear()
        self._nc = None

