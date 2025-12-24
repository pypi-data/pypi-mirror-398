"""Runtime orchestration for HexSwitch."""

import asyncio
import signal
from typing import Any

from hexswitch.adapters.base import InboundAdapter, OutboundAdapter
from hexswitch.adapters.exceptions import AdapterError
from hexswitch.handlers.loader import HandlerLoader
from hexswitch.pipeline.middleware.backpressure import BackpressureMiddleware
from hexswitch.pipeline.middleware.observability import ObservabilityMiddleware
from hexswitch.pipeline.middleware.retry import RetryMiddleware
from hexswitch.pipeline.middleware.timeout import TimeoutMiddleware
from hexswitch.pipeline.middleware.trace import (
    TraceExtractionMiddleware,
    TraceInjectionMiddleware,
)
from hexswitch.pipeline.pipeline import Pipeline
from hexswitch.ports.outbound_registry import OutboundPortRegistry
from hexswitch.ports.registry import get_port_registry
from hexswitch.registry.adapters import ADAPTER_METADATA, AdapterRegistry
from hexswitch.registry.factory import AdapterFactory
from hexswitch.routing.routes import OutboundRouteRegistry
from hexswitch.shared.config.config import build_execution_plan
from hexswitch.shared.envelope import Envelope
from hexswitch.shared.logging import get_logger
from hexswitch.shared.observability import (
    get_global_metrics_collector,
    get_global_tracer,
    start_span,
)

logger = get_logger(__name__)


class Runtime:
    """Runtime orchestrator for HexSwitch adapters."""

    def __init__(self, config: dict[str, Any]):
        """Initialize runtime.

        Args:
            config: Configuration dictionary.
        """
        self.config = config
        self.inbound_adapters: list[InboundAdapter] = []
        self.outbound_adapters: list[OutboundAdapter] = []
        self._shutdown_requested = False

        # Initialize registries and factories
        self.adapter_registry = AdapterRegistry()
        self.adapter_factory = AdapterFactory()
        self.handler_loader = HandlerLoader()
        self.outbound_registry = OutboundPortRegistry()
        self.route_registry = OutboundRouteRegistry()

        # Initialize execution model
        self._loop: asyncio.AbstractEventLoop | None = None
        self._executor: Any | None = None  # ThreadPoolExecutor for blocking operations
        self._shutdown_event: asyncio.Event | None = None
        self._running_tasks: list[asyncio.Task] = []
        self._registered_ports: list[str] = []  # Track ports registered by this runtime

        # Initialize GUI server if enabled
        gui_config = self.config.get("service", {}).get("gui", {})
        if gui_config.get("enabled", False):
            from hexswitch.gui import GuiServer
            self.gui_server = GuiServer(config=gui_config, runtime=self)
        else:
            self.gui_server = None

        # Initialize pipeline
        self.pipeline = Pipeline(self)
        # Add middleware in order (execution is reversed)
        self.pipeline.add_middleware(TraceInjectionMiddleware())  # Last (injects after processing)
        self.pipeline.add_middleware(ObservabilityMiddleware())  # Middle (observability)
        self.pipeline.add_middleware(TraceExtractionMiddleware())  # First (extracts before processing)

        # Load port policies from config
        self._load_port_policies()

        # Initialize observability
        self._tracer = get_global_tracer()
        self._metrics = get_global_metrics_collector()

        # Runtime metrics
        self._runtime_start_time: float | None = None
        self._adapter_start_counter = self._metrics.counter("runtime_adapter_starts_total")
        self._adapter_stop_counter = self._metrics.counter("runtime_adapter_stops_total")
        self._adapter_error_counter = self._metrics.counter("runtime_adapter_errors_total")
        self._adapter_start_duration = self._metrics.histogram("runtime_adapter_start_duration_seconds")
        self._active_adapters_gauge = self._metrics.gauge("runtime_active_adapters_total")

    def _create_inbound_adapter(
        self, name: str, adapter_config: dict[str, Any]
    ) -> InboundAdapter:
        """Create an inbound adapter instance.

        Args:
            name: Adapter name (e.g., 'http', 'grpc', 'websocket')
            adapter_config: Adapter-specific configuration

        Returns:
            InboundAdapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        try:
            adapter = self.adapter_factory.create_inbound_adapter(name, adapter_config)
            return adapter
        except KeyError as e:
            raise AdapterError(f"Unknown inbound adapter: {name}") from e
        except AdapterError:
            # Re-raise AdapterError as-is (e.g., "Unknown adapter")
            raise
        except Exception as e:
            raise AdapterError(f"Failed to create inbound adapter '{name}': {e}") from e

    def _create_outbound_adapter(
        self, name: str, adapter_config: dict[str, Any]
    ) -> OutboundAdapter:
        """Create an outbound adapter instance.

        Args:
            name: Adapter name (e.g., 'http_client', 'grpc_client')
            adapter_config: Adapter-specific configuration

        Returns:
            OutboundAdapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        try:
            adapter = self.adapter_factory.create_outbound_adapter(name, adapter_config)
            return adapter
        except KeyError as e:
            raise AdapterError(f"Unknown outbound adapter: {name}") from e
        except Exception as e:
            raise AdapterError(f"Failed to create outbound adapter '{name}': {e}") from e

    def start(self) -> None:
        """Start all enabled adapters (synchronous entry point).

        Raises:
            RuntimeError: If adapter startup fails.
        """
        # Create or get event loop
        try:
            self._loop = asyncio.get_event_loop()
            # Check if loop is closed, create new one if so
            if self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        # Initialize shutdown event
        self._shutdown_event = asyncio.Event()

        # Run async start
        self._loop.run_until_complete(self._async_start())

    async def _async_start(self) -> None:
        """Start all enabled adapters (async implementation).

        Raises:
            RuntimeError: If adapter startup fails.
        """
        import time

        span = start_span("runtime.start", tags={"service": self.config.get("service", {}).get("name", "unknown")})
        self._runtime_start_time = time.time()

        try:
            plan = build_execution_plan(self.config)

            # Start inbound adapters
            for adapter_info in plan["inbound_adapters"]:
                adapter_span = start_span(
                    "adapter.start",
                    parent=span,
                    tags={"adapter": adapter_info["name"], "type": "inbound"},
                )
                start_time = time.time()
                try:
                    inbound_adapter: InboundAdapter = self._create_inbound_adapter(
                        adapter_info["name"], adapter_info["config"]
                    )
                    # Set handler loader and runtime references
                    if hasattr(inbound_adapter, "_handler_loader"):
                        inbound_adapter._handler_loader = self.handler_loader
                    if hasattr(inbound_adapter, "_runtime"):
                        inbound_adapter._runtime = self
                    # Start adapter using appropriate runner
                    await self._start_adapter(inbound_adapter)
                    self.inbound_adapters.append(inbound_adapter)
                    duration = time.time() - start_time
                    self._adapter_start_duration.observe(duration)
                    self._adapter_start_counter.inc()
                    self._active_adapters_gauge.set(len(self.inbound_adapters) + len(self.outbound_adapters))
                    adapter_span.add_tag("status", "success")
                    logger.info(f"Started inbound adapter: {adapter_info['name']}")
                except Exception as e:
                    self._adapter_error_counter.inc()
                    adapter_span.add_tag("status", "error")
                    adapter_span.add_tag("error", str(e))
                    logger.error(f"Failed to start inbound adapter '{adapter_info['name']}': {e}")
                    raise RuntimeError(f"Failed to start adapter '{adapter_info['name']}'") from e
                finally:
                    adapter_span.finish()

            # Start outbound adapters
            for adapter_info in plan["outbound_adapters"]:
                adapter_span = start_span(
                    "adapter.start",
                    parent=span,
                    tags={"adapter": adapter_info["name"], "type": "outbound"},
                )
                start_time = time.time()
                try:
                    outbound_adapter: OutboundAdapter = self._create_outbound_adapter(
                        adapter_info["name"], adapter_info["config"]
                    )
                    # Start adapter using appropriate runner
                    await self._start_adapter(outbound_adapter)
                    self.outbound_adapters.append(outbound_adapter)
                    duration = time.time() - start_time
                    self._adapter_start_duration.observe(duration)
                    self._adapter_start_counter.inc()
                    self._active_adapters_gauge.set(len(self.inbound_adapters) + len(self.outbound_adapters))
                    adapter_span.add_tag("status", "success")
                    logger.info(f"Started outbound adapter: {adapter_info['name']}")
                except Exception as e:
                    self._adapter_error_counter.inc()
                    adapter_span.add_tag("status", "error")
                    adapter_span.add_tag("error", str(e))
                    logger.error(f"Failed to start outbound adapter '{adapter_info['name']}': {e}")
                    raise RuntimeError(f"Failed to start adapter '{adapter_info['name']}'") from e
                finally:
                    adapter_span.finish()

            # Start outbound adapters and bind to ports (legacy compatibility)
            port_registry = get_port_registry()
            # Map adapter names to their configs for port lookup
            adapter_config_map = {
                adapter_info["name"]: adapter_info["config"]
                for adapter_info in plan["outbound_adapters"]
            }
            for outbound_adapter in self.outbound_adapters:
                # Get port names from adapter config first, fallback to metadata
                adapter_config = adapter_config_map.get(outbound_adapter.name, {})
                port_names = adapter_config.get("ports", [])

                # Support both string and list for ports
                if isinstance(port_names, str):
                    port_names = [port_names]
                elif not port_names:
                    adapter_metadata = ADAPTER_METADATA.get(outbound_adapter.name, {})
                    port_names = adapter_metadata.get("outbound_ports", [])

                # Register adapter as handler for each port
                for port_name in port_names:
                    def create_adapter_handler(adapter_instance: OutboundAdapter):
                        def handler(envelope):
                            return adapter_instance.request(envelope)
                        return handler
                    handler = create_adapter_handler(outbound_adapter)
                    port_registry.register_handler(port_name, handler)
                    # Track registered ports for cleanup
                    if port_name not in self._registered_ports:
                        self._registered_ports.append(port_name)

            # Start GUI server if enabled
            if self.gui_server:
                self.gui_server.start()

            span.add_tag("status", "success")
            logger.info("Runtime started successfully")
        except Exception as e:
            span.add_tag("status", "error")
            span.add_tag("error", str(e))
            logger.error(f"Runtime startup failed: {e}")
            raise RuntimeError(f"Runtime startup failed: {e}") from e
        finally:
            span.finish()

    async def _start_adapter(self, adapter: InboundAdapter | OutboundAdapter) -> None:
        """Start an adapter using the appropriate runner.

        Args:
            adapter: Adapter instance to start
        """
        # For inbound adapters, call start() to start servers/threads
        # For outbound adapters, call connect() to establish connections
        loop = asyncio.get_event_loop()
        if self._executor is None:
            from concurrent.futures import ThreadPoolExecutor
            self._executor = ThreadPoolExecutor(max_workers=10)

        if isinstance(adapter, InboundAdapter):
            # Start adapter in executor - this should return quickly after starting threads
            await loop.run_in_executor(self._executor, adapter.start)
            # Give adapter a moment to initialize (especially for server threads)
            await asyncio.sleep(0.1)
        elif isinstance(adapter, OutboundAdapter):
            # Connect outbound adapter in executor
            await loop.run_in_executor(self._executor, adapter.connect)

    async def _stop_adapter(self, adapter: InboundAdapter | OutboundAdapter) -> None:
        """Stop an adapter using the appropriate runner.

        Args:
            adapter: Adapter instance to stop
        """
        # Stop adapter in executor to avoid blocking
        loop = asyncio.get_event_loop()
        if self._executor:
            if isinstance(adapter, InboundAdapter):
                await loop.run_in_executor(self._executor, adapter.stop)
            elif isinstance(adapter, OutboundAdapter):
                await loop.run_in_executor(self._executor, adapter.disconnect)

    def stop(self) -> None:
        """Stop all adapters gracefully (synchronous entry point)."""
        # If loop is closed or doesn't exist, create a new one for cleanup
        if self._loop and not self._loop.is_closed():
            try:
                self._loop.run_until_complete(self._async_stop())
            except RuntimeError as e:
                # Event loop might have been closed during execution
                if "Event loop is closed" in str(e) or "loop is closed" in str(e).lower():
                    logger.warning("Event loop was closed during stop, creating new loop for cleanup")
                    self._loop = None
                else:
                    raise
        else:
            # Loop is closed or doesn't exist, create a new one for cleanup
            logger.debug("Event loop is closed or doesn't exist, creating new loop for cleanup")
            self._loop = None

        # If we still need to clean up (loop was closed), create a new loop
        if self._loop is None and (self.inbound_adapters or self.outbound_adapters or self.gui_server):
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._loop.run_until_complete(self._async_stop())
            finally:
                # Clean up the temporary loop
                if self._loop:
                    try:
                        # Cancel any remaining tasks
                        pending = asyncio.all_tasks(self._loop)
                        for task in pending:
                            task.cancel()
                        # Wait for tasks to be cancelled
                        if pending:
                            self._loop.run_until_complete(
                                asyncio.gather(*pending, return_exceptions=True)
                            )
                    except Exception:
                        pass
                    finally:
                        self._loop.close()
                        self._loop = None

    async def _async_stop(self) -> None:
        """Stop all adapters gracefully (async implementation)."""
        import time

        # If already stopped and adapters are cleared, return early
        if self._shutdown_requested and len(self.inbound_adapters) == 0 and len(self.outbound_adapters) == 0:
            return

        self._shutdown_requested = True
        logger.info("Stopping runtime...")

        span = start_span("runtime.stop", tags={"service": self.config.get("service", {}).get("name", "unknown")})

        try:
            # Signal shutdown
            if self._shutdown_event:
                self._shutdown_event.set()

            # Cancel all running tasks
            for task in self._running_tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete (with timeout)
            if self._running_tasks:
                await asyncio.wait(self._running_tasks, timeout=5.0, return_when=asyncio.ALL_COMPLETED)

            # Stop inbound adapters
            inbound_adapters_to_stop = list(self.inbound_adapters)
            for adapter in inbound_adapters_to_stop:
                try:
                    await self._stop_adapter(adapter)
                    # Also call adapter.stop() directly for compatibility
                    if hasattr(adapter, "stop"):
                        try:
                            adapter.stop()
                        except Exception:
                            pass  # Ignore if already stopped
                    self._adapter_stop_counter.inc()
                    logger.info(f"Stopped inbound adapter: {adapter.name}")
                except Exception as e:
                    logger.error(f"Error stopping inbound adapter '{adapter.name}': {e}")
            # Clear inbound adapters list
            self.inbound_adapters.clear()

            # Stop outbound adapters
            outbound_adapters_to_stop = list(self.outbound_adapters)
            for adapter in outbound_adapters_to_stop:
                try:
                    await self._stop_adapter(adapter)
                    # _stop_adapter already calls disconnect(), no need to call it again
                    self._adapter_stop_counter.inc()
                    logger.info(f"Stopped outbound adapter: {adapter.name}")
                except Exception as e:
                    logger.error(f"Error stopping outbound adapter '{adapter.name}': {e}")
            # Clear outbound adapters list
            self.outbound_adapters.clear()

            # Remove ports that were registered by this runtime
            # This prevents port conflicts between test runs
            port_registry = get_port_registry()
            for port_name in self._registered_ports:
                try:
                    port = port_registry.get_port(port_name)
                    if port:
                        # Remove all handlers from this port
                        port.handlers.clear()
                        # Remove the port itself
                        with port_registry._lock:
                            port_registry._ports.pop(port_name, None)
                except Exception as e:
                    logger.debug(f"Error removing port '{port_name}': {e}")
            self._registered_ports.clear()

            # Stop GUI server
            if self.gui_server:
                try:
                    self.gui_server.stop()
                except Exception as e:
                    logger.error(f"Error stopping GUI server: {e}")

            # Shutdown executor
            if self._executor:
                self._executor.shutdown(wait=True)

            # Calculate runtime duration
            if self._runtime_start_time:
                duration = time.time() - self._runtime_start_time
                logger.info(f"Runtime was active for {duration:.2f} seconds")

            span.add_tag("status", "success")
            logger.info("Runtime stopped successfully")
        except Exception as e:
            span.add_tag("status", "error")
            span.add_tag("error", str(e))
            logger.error(f"Error during runtime shutdown: {e}")
        finally:
            span.finish()
            self._active_adapters_gauge.set(0)

    def emit(self, envelope: Envelope) -> Envelope:
        """Emit an envelope to an outbound target.

        Args:
            envelope: Envelope to emit

        Returns:
            Response envelope
        """
        # Find route for envelope
        port_name = envelope.metadata.get("port_name") or envelope.path
        targets = self.route_registry.match_route(port_name)

        if targets:
            target = self.route_registry.select_target(port_name, envelope)
            return self.deliver(envelope, target.adapter_name)
        else:
            # No route found, return error
            logger.warning(f"No route found for port '{port_name}'")
            return Envelope.error(404, f"No route found for port '{port_name}'")

    def deliver(self, envelope: Envelope, target_adapter_name: str) -> Envelope:
        """Deliver an envelope to a specific outbound adapter.

        Args:
            envelope: Envelope to deliver
            target_adapter_name: Name of target adapter

        Returns:
            Response envelope
        """
        # Find adapter
        adapter = None
        for outbound_adapter in self.outbound_adapters:
            if outbound_adapter.name == target_adapter_name:
                adapter = outbound_adapter
                break

        if not adapter:
            logger.error(f"Outbound adapter '{target_adapter_name}' not found")
            return Envelope.error(404, f"Adapter '{target_adapter_name}' not found")

        if not isinstance(adapter, OutboundAdapter):
            raise ValueError(f"Adapter '{target_adapter_name}' is not an OutboundAdapter")

        # Send request and return response
        try:
            return adapter.request(envelope)
        except Exception as e:
            logger.error(f"Failed to deliver envelope to '{target_adapter_name}': {e}")
            return Envelope.error(500, f"Failed to deliver: {e}")

    async def run(self) -> None:
        """Run the runtime event loop (async).

        This method blocks until shutdown is requested (via signal or stop()).
        """
        if not self._loop:
            raise RuntimeError("Runtime not started. Call start() first.")

        logger.info("Runtime event loop started")
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self._async_stop()

    def run_sync(self) -> None:
        """Run the runtime event loop (synchronous, blocking).

        This method blocks until shutdown is requested (via signal or stop()).
        """
        if not self._loop:
            raise RuntimeError("Runtime not started. Call start() first.")

        logger.info("Runtime event loop started")
        try:
            # Run event loop until shutdown
            self._loop.run_until_complete(self.run())
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()

    def _load_port_policies(self) -> None:
        """Load port policies from config and configure middleware."""
        if not hasattr(self, "config") or not self.config:
            return

        ports_config = self.config.get("ports", {})
        if not ports_config:
            return

        for port_name, port_config in ports_config.items():
            policy_dict: dict[str, Any] = {}

            # Extract policies
            if isinstance(port_config, dict):
                policies = port_config.get("policies", {})
                if policies:
                    if isinstance(policies, dict):
                        policy_dict["retry"] = policies.get("retry")
                        policy_dict["timeout"] = policies.get("timeout")
                        policy_dict["backpressure"] = policies.get("backpressure")

            # Store policy for this port
            if policy_dict:
                self.pipeline.set_port_policy(port_name, policy_dict)

    async def dispatch(self, envelope: Envelope) -> Envelope:
        """Dispatch envelope through pipeline (async entry point for inbound adapters).

        Args:
            envelope: Request envelope

        Returns:
            Response envelope
        """
        # Get port name from envelope metadata
        port_name = envelope.metadata.get("port_name")

        # Add port-specific middleware if policies exist
        port_policy = self.pipeline.get_port_policy(port_name)
        if port_policy:
            # Create temporary middleware stack with port-specific middleware
            original_stack = self.pipeline.middleware_stack.copy()

            # Add port-specific middleware in order (will be reversed during execution)
            if port_policy.get("backpressure"):
                self.pipeline.add_middleware(
                    BackpressureMiddleware(port_policy["backpressure"])
                )
            if port_policy.get("timeout"):
                self.pipeline.add_middleware(TimeoutMiddleware(port_policy["timeout"]))
            if port_policy.get("retry"):
                self.pipeline.add_middleware(RetryMiddleware(port_policy["retry"]))

            try:
                result = await self.pipeline.process(envelope)
            finally:
                # Restore original middleware stack
                self.pipeline.middleware_stack = original_stack

            return result

        return await self.pipeline.process(envelope)

    def request_shutdown(self) -> None:
        """Request graceful shutdown of the runtime."""
        self._shutdown_requested = True
        if self._shutdown_event:
            self._shutdown_event.set()


def run_runtime(config: dict[str, Any]) -> None:
    """Start the runtime event loop.

    Args:
        config: Configuration dictionary.

    Raises:
        RuntimeError: If runtime fails to start.
    """
    runtime = Runtime(config)

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum: int, frame: Any) -> None:
        logger.info(f"Received signal {signum}, initiating shutdown...")
        runtime.request_shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        runtime.start()
        runtime.run_sync()
    except Exception as e:
        logger.error(f"Runtime error: {e}")
        runtime.stop()
        raise RuntimeError(f"Runtime execution failed: {e}") from e
