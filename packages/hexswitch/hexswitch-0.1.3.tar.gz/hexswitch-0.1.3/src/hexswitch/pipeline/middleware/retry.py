"""Retry middleware for pipeline processing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from hexswitch.pipeline.pipeline import PipelineContext

logger = logging.getLogger(__name__)


class RetryMiddleware:
    """Middleware that retries failed requests based on policy."""

    def __init__(self, policy: dict[str, Any] | None = None):
        """Initialize retry middleware.

        Args:
            policy: Retry policy configuration
        """
        self.policy = policy or {}
        self.enabled = self.policy.get("enabled", False)
        self.max_attempts = self.policy.get("max_attempts", 3)
        self.initial_delay = self.policy.get("initial_delay", 1.0)
        self.max_delay = self.policy.get("max_delay", 60.0)
        self.backoff_multiplier = self.policy.get("backoff_multiplier", 2.0)
        self.retryable_errors = self.policy.get(
            "retryable_errors", ["500", "502", "503", "504", "timeout"]
        )

    def _is_retryable(self, ctx: PipelineContext) -> bool:
        """Check if error is retryable.

        Args:
            ctx: Pipeline context

        Returns:
            True if error is retryable
        """
        if not ctx.envelope.error_message:
            return False

        status_code = ctx.envelope.status_code
        error_message = ctx.envelope.error_message.lower()

        # Check status code
        if str(status_code) in self.retryable_errors:
            return True

        # Check error message
        for retryable in self.retryable_errors:
            if retryable.lower() in error_message:
                return True

        return False

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Execute middleware with retry logic.

        Args:
            ctx: Pipeline context
            next: Next middleware in chain

        Returns:
            Updated context
        """
        if not self.enabled:
            return await next(ctx)

        attempt = 0
        delay = self.initial_delay

        while attempt < self.max_attempts:
            try:
                # Execute next middleware
                result_ctx = await next(ctx)

                # Check if successful
                if not result_ctx.envelope.error_message:
                    return result_ctx

                # Check if error is retryable
                if not self._is_retryable(result_ctx):
                    logger.debug(
                        f"Error not retryable: {result_ctx.envelope.error_message}"
                    )
                    return result_ctx

                attempt += 1
                if attempt >= self.max_attempts:
                    logger.warning(
                        f"Max retry attempts ({self.max_attempts}) reached for {ctx.port_name}"
                    )
                    return result_ctx

                # Wait before retry
                logger.info(
                    f"Retrying {ctx.port_name} (attempt {attempt}/{self.max_attempts}) after {delay}s"
                )
                await asyncio.sleep(delay)

                # Exponential backoff
                delay = min(delay * self.backoff_multiplier, self.max_delay)

                # Reset context for retry (clear error)
                ctx.envelope.error_message = None
                ctx.envelope.status_code = 200

            except Exception as e:
                attempt += 1
                if attempt >= self.max_attempts:
                    logger.exception(f"Max retry attempts reached, re-raising: {e}")
                    raise

                # Check if exception is retryable
                error_str = str(e).lower()
                is_retryable = any(
                    retryable.lower() in error_str for retryable in self.retryable_errors
                )

                if not is_retryable:
                    logger.debug(f"Exception not retryable: {e}")
                    raise

                # Wait before retry
                logger.info(
                    f"Retrying after exception (attempt {attempt}/{self.max_attempts}) after {delay}s"
                )
                await asyncio.sleep(delay)

                # Exponential backoff
                delay = min(delay * self.backoff_multiplier, self.max_delay)

        return ctx


