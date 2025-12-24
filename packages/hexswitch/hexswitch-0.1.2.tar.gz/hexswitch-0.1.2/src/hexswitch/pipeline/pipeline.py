"""Canonical pipeline for message processing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import inspect
import logging
from typing import Any, Callable

from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Context passed through pipeline stages."""

    envelope: Envelope
    port_name: str | None = None
    stage: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class Pipeline:
    """Canonical pipeline for processing envelopes through defined stages."""

    def __init__(self, runtime: Any):
        """Initialize pipeline.

        Args:
            runtime: Runtime instance (for accessing registries, handlers, etc.)
        """
        self.runtime = runtime
        self.middleware_stack: list[Callable] = []
        self._concurrency_gates: dict[str, asyncio.Semaphore] = {}
        self._port_policies: dict[str, dict[str, Any]] = {}

    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the stack.

        Args:
            middleware: Middleware callable (async function that takes ctx and next)
        """
        self.middleware_stack.append(middleware)

    def set_port_policy(self, port_name: str, policy: dict[str, Any]) -> None:
        """Set policy for a specific port.

        Args:
            port_name: Port name
            policy: Policy configuration dictionary
        """
        self._port_policies[port_name] = policy

    def get_port_policy(self, port_name: str | None) -> dict[str, Any]:
        """Get policy for a specific port.

        Args:
            port_name: Port name

        Returns:
            Policy configuration dictionary
        """
        if not port_name:
            return {}
        return self._port_policies.get(port_name, {})

    async def process(self, envelope: Envelope) -> Envelope:
        """Process envelope through pipeline.

        Args:
            envelope: Input envelope

        Returns:
            Processed envelope
        """
        ctx = PipelineContext(envelope=envelope, stage="ingress")

        # Create middleware chain
        async def final_handler(ctx: PipelineContext) -> PipelineContext:
            """Final handler that executes pipeline stages."""
            # Stage 1: Normalize/Enrich
            ctx = await self._normalize(ctx)

            # Stage 2: Telemetry span start
            ctx = await self._start_telemetry(ctx)

            # Stage 3: Validation
            ctx = await self._validate(ctx)

            # Stage 4: Inbound routing
            ctx = await self._route_inbound(ctx)

            # Stage 5: Execute handler (with concurrency gates)
            ctx = await self._execute_handler(ctx)

            # Stage 6: Error mapping
            ctx = await self._map_errors(ctx)

            # Stage 7: Outbound routing (if needed)
            ctx = await self._route_outbound(ctx)

            # Stage 8: Finish telemetry
            ctx = await self._finish_telemetry(ctx)

            return ctx

        # Build middleware chain (execute in reverse order)
        handler = final_handler
        for middleware in reversed(self.middleware_stack):
            # Capture current handler in closure
            next_handler = handler

            def create_middleware_wrapper(mw, next_h):
                async def wrapper(ctx: PipelineContext) -> PipelineContext:
                    return await mw(ctx, next_h)
                return wrapper

            handler = create_middleware_wrapper(middleware, next_handler)

        try:
            # Execute middleware chain
            ctx = await handler(ctx)
            return ctx.envelope

        except Exception as e:
            logger.exception(f"Pipeline error in stage '{ctx.stage}': {e}")
            ctx.metadata["exception"] = e
            ctx = await self._map_errors(ctx)
            return ctx.envelope

    async def _normalize(self, ctx: PipelineContext) -> PipelineContext:
        """Normalize and enrich envelope.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context
        """
        ctx.stage = "normalize"
        # Ensure envelope has required fields
        if not ctx.envelope.headers:
            ctx.envelope.headers = {}
        if not ctx.envelope.metadata:
            ctx.envelope.metadata = {}
        if not ctx.envelope.path_params:
            ctx.envelope.path_params = {}
        if not ctx.envelope.query_params:
            ctx.envelope.query_params = {}
        return ctx

    async def _start_telemetry(self, ctx: PipelineContext) -> PipelineContext:
        """Start telemetry span.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context
        """
        ctx.stage = "telemetry.start"
        # Telemetry will be handled by middleware
        # This is a placeholder for now
        return ctx

    async def _validate(self, ctx: PipelineContext) -> PipelineContext:
        """Validate envelope.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context
        """
        ctx.stage = "validate"
        # Validation will be handled by middleware
        # This is a placeholder for now
        return ctx

    async def _route_inbound(self, ctx: PipelineContext) -> PipelineContext:
        """Route to inbound handler.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context with port_name set
        """
        ctx.stage = "route.inbound"
        # Routing logic will be handled by middleware or here
        # For now, extract port_name from envelope metadata if available
        if not ctx.port_name:
            ctx.port_name = ctx.envelope.metadata.get("port_name")
        return ctx

    def _get_semaphore(self, port_name: str) -> asyncio.Semaphore:
        """Get or create semaphore for port concurrency control.

        Args:
            port_name: Port name

        Returns:
            Semaphore for the port
        """
        if port_name not in self._concurrency_gates:
            # Get max_concurrent from config, default to 10
            max_concurrent = 10
            if hasattr(self.runtime, "config"):
                ports_config = self.runtime.config.get("ports", {})
                port_config = ports_config.get(port_name, {})
                max_concurrent = port_config.get("max_concurrent", 10)

            self._concurrency_gates[port_name] = asyncio.Semaphore(max_concurrent)

        return self._concurrency_gates[port_name]

    async def _execute_handler(self, ctx: PipelineContext) -> PipelineContext:
        """Execute handler with concurrency gates.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context with handler result
        """
        ctx.stage = "handler.execute"

        if not ctx.port_name:
            logger.warning("No port_name in context, cannot execute handler")
            ctx.envelope = Envelope.error(400, "No port specified")
            return ctx

        # Get handler via handler loader
        try:
            handler = self.runtime.handler_loader.resolve(ctx.port_name)
        except Exception as e:
            logger.error(f"Failed to load handler for port '{ctx.port_name}': {e}")
            ctx.envelope = Envelope.error(500, f"Handler not found: {ctx.port_name}")
            return ctx

        # Execute handler with concurrency gate
        semaphore = self._get_semaphore(ctx.port_name)
        async with semaphore:
            try:
                # Execute handler (may be sync or async)
                if inspect.iscoroutinefunction(handler):
                    response = await handler(ctx.envelope)
                else:
                    # Run sync handler in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, handler, ctx.envelope)

                if isinstance(response, Envelope):
                    ctx.envelope = response
                else:
                    logger.warning(f"Handler returned non-Envelope: {type(response)}")
                    ctx.envelope = Envelope.success(response if response else {})
            except Exception as e:
                logger.exception(f"Handler execution error: {e}")
                ctx.metadata["exception"] = e
                ctx.envelope = Envelope.error(500, str(e))

        return ctx

    async def _map_errors(self, ctx: PipelineContext) -> PipelineContext:
        """Map exceptions to error envelopes.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context
        """
        ctx.stage = "error.map"

        # Check for exceptions in metadata
        if "exception" in ctx.metadata:
            exc = ctx.metadata["exception"]
            if not ctx.envelope.error_message:
                ctx.envelope = Envelope.error(
                    status_code=500,
                    error=str(exc),
                )
                ctx.envelope.metadata["error.type"] = type(exc).__name__

        return ctx

    async def _route_outbound(self, ctx: PipelineContext) -> PipelineContext:
        """Route to outbound if needed.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context
        """
        ctx.stage = "route.outbound"
        # Outbound routing will be handled by middleware or here
        # This is a placeholder for now
        return ctx

    async def _finish_telemetry(self, ctx: PipelineContext) -> PipelineContext:
        """Finish telemetry span.

        Args:
            ctx: Pipeline context

        Returns:
            Updated context
        """
        ctx.stage = "telemetry.finish"
        # Telemetry will be handled by middleware
        # This is a placeholder for now
        return ctx

