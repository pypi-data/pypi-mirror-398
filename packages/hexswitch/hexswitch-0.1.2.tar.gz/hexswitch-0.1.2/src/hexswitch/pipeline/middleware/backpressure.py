"""Backpressure middleware for pipeline processing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from hexswitch.pipeline.pipeline import PipelineContext
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class BackpressureMiddleware:
    """Middleware that enforces backpressure limits."""

    def __init__(self, policy: dict[str, Any] | None = None):
        """Initialize backpressure middleware.

        Args:
            policy: Backpressure policy configuration
        """
        self.policy = policy or {}
        self.enabled = self.policy.get("enabled", False)
        self.max_concurrent = self.policy.get("max_concurrent", 10)
        self.queue_size = self.policy.get("queue_size", 100)
        self.rejection_strategy = self.policy.get("rejection_strategy", "fail_fast")

        # Semaphore for concurrent requests
        self._semaphore: asyncio.Semaphore | None = None
        # Queue for queuing strategy
        self._queue: asyncio.Queue | None = None

        if self.enabled:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
            if self.rejection_strategy == "queue":
                self._queue = asyncio.Queue(maxsize=self.queue_size)

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Execute middleware with backpressure control.

        Args:
            ctx: Pipeline context
            next: Next middleware in chain

        Returns:
            Updated context
        """
        if not self.enabled or not self._semaphore:
            return await next(ctx)

        # Check if we can accept the request
        if self.rejection_strategy == "fail_fast":
            # Try to acquire semaphore immediately
            if not self._semaphore.locked() or self._semaphore._value > 0:
                async with self._semaphore:
                    return await next(ctx)
            else:
                # Reject immediately
                logger.warning(
                    f"Backpressure limit reached, rejecting request for {ctx.port_name or 'unknown'}"
                )
                ctx.envelope = Envelope.error(503, "Service temporarily unavailable (backpressure)")
                ctx.metadata["backpressure_rejected"] = True
                return ctx

        elif self.rejection_strategy == "queue":
            # Queue the request
            if self._queue and self._queue.full():
                logger.warning(
                    f"Backpressure queue full, rejecting request for {ctx.port_name or 'unknown'}"
                )
                ctx.envelope = Envelope.error(503, "Service temporarily unavailable (queue full)")
                ctx.metadata["backpressure_rejected"] = True
                return ctx

            # Add to queue and process
            await self._queue.put(ctx)
            async with self._semaphore:
                try:
                    queued_ctx = await self._queue.get()
                    return await next(queued_ctx)
                finally:
                    self._queue.task_done()

        elif self.rejection_strategy == "drop":
            # Drop silently if limit reached
            if self._semaphore._value == 0:
                logger.debug(
                    f"Backpressure limit reached, dropping request for {ctx.port_name or 'unknown'}"
                )
                ctx.envelope = Envelope.error(503, "Service temporarily unavailable")
                ctx.metadata["backpressure_dropped"] = True
                return ctx

            async with self._semaphore:
                return await next(ctx)

        else:
            # Unknown strategy, just execute
            logger.warning(f"Unknown backpressure strategy: {self.rejection_strategy}")
            return await next(ctx)


