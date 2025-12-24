"""Timeout middleware for pipeline processing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from hexswitch.pipeline.pipeline import PipelineContext
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class TimeoutMiddleware:
    """Middleware that enforces timeouts on request processing."""

    def __init__(self, policy: dict[str, Any] | None = None):
        """Initialize timeout middleware.

        Args:
            policy: Timeout policy configuration
        """
        self.policy = policy or {}
        self.enabled = self.policy.get("enabled", False)
        self.timeout_seconds = self.policy.get("timeout_seconds", 30.0)

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Execute middleware with timeout.

        Args:
            ctx: Pipeline context
            next: Next middleware in chain

        Returns:
            Updated context
        """
        if not self.enabled:
            return await next(ctx)

        try:
            # Execute with timeout
            result_ctx = await asyncio.wait_for(
                next(ctx), timeout=self.timeout_seconds
            )
            return result_ctx

        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout after {self.timeout_seconds}s for {ctx.port_name or 'unknown'}"
            )
            ctx.envelope = Envelope.error(
                504, f"Request timeout after {self.timeout_seconds}s"
            )
            ctx.metadata["timeout"] = True
            return ctx

        except Exception:
            # Re-raise other exceptions
            raise


