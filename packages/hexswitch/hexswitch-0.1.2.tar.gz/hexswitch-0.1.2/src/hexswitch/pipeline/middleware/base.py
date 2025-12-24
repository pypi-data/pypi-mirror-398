"""Base middleware interface for pipeline processing."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from hexswitch.pipeline.pipeline import PipelineContext


class Middleware(Protocol):
    """Protocol for pipeline middleware.

    Middleware functions process pipeline context and can call the next middleware
    in the chain.
    """

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Execute middleware.

        Args:
            ctx: Pipeline context
            next: Next middleware in chain (or final handler)

        Returns:
            Updated context
        """
        ...

