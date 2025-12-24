"""Trace context extraction and injection middleware."""

from __future__ import annotations

import logging
from typing import Any, Callable

from hexswitch.pipeline.pipeline import PipelineContext

logger = logging.getLogger(__name__)


def parse_traceparent(traceparent: str) -> tuple[str, str, str | None]:
    """Parse W3C traceparent header.

    Format: 00-{trace_id}-{span_id}-{flags}
    trace_id: 32 hex characters
    span_id: 16 hex characters
    flags: 2 hex characters

    Args:
        traceparent: W3C traceparent header value

    Returns:
        Tuple of (trace_id, span_id, parent_span_id)
    """
    parts = traceparent.split("-")
    if len(parts) != 4:
        raise ValueError(f"Invalid traceparent format: {traceparent}")

    version = parts[0]
    if version != "00":
        logger.warning(f"Unsupported traceparent version: {version}")

    trace_id = parts[1]
    span_id = parts[2]
    parts[3]

    # For now, parent_span_id is None (could be extracted from flags or other headers)
    parent_span_id = None

    return trace_id, span_id, parent_span_id


def format_traceparent(trace_id: str, span_id: str, parent_span_id: str | None = None) -> str:
    """Format W3C traceparent header.

    Args:
        trace_id: Trace ID (32 hex characters)
        span_id: Span ID (16 hex characters)
        parent_span_id: Parent span ID (optional)

    Returns:
        W3C traceparent header value
    """
    flags = "01"  # Default flags (sampled)
    return f"00-{trace_id}-{span_id}-{flags}"


class TraceExtractionMiddleware:
    """Extract trace context from envelope headers/metadata."""

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Extract trace context from envelope headers/metadata.

        Args:
            ctx: Pipeline context
            next: Next middleware in chain

        Returns:
            Updated context
        """
        # Extract W3C Trace Context from headers
        traceparent = ctx.envelope.headers.get("traceparent")
        if traceparent:
            try:
                trace_id, span_id, parent_span_id = parse_traceparent(traceparent)
                ctx.envelope.trace_id = trace_id
                ctx.envelope.span_id = span_id
                ctx.envelope.parent_span_id = parent_span_id
                logger.debug(f"Extracted trace context: trace_id={trace_id}, span_id={span_id}")
            except Exception as e:
                logger.warning(f"Failed to parse traceparent header: {e}")

        # Also check metadata for trace context (for non-HTTP protocols)
        if not ctx.envelope.trace_id and ctx.envelope.metadata.get("trace_id"):
            ctx.envelope.trace_id = ctx.envelope.metadata.get("trace_id")
            ctx.envelope.span_id = ctx.envelope.metadata.get("span_id")
            ctx.envelope.parent_span_id = ctx.envelope.metadata.get("parent_span_id")

        return await next(ctx)


class TraceInjectionMiddleware:
    """Inject trace context into envelope headers/metadata."""

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Inject trace context into envelope headers/metadata.

        Args:
            ctx: Pipeline context
            next: Next middleware in chain

        Returns:
            Updated context
        """
        # Call next middleware first
        ctx = await next(ctx)

        # Inject W3C Trace Context into headers if trace_id exists
        if ctx.envelope.trace_id and ctx.envelope.span_id:
            traceparent = format_traceparent(
                ctx.envelope.trace_id,
                ctx.envelope.span_id,
                ctx.envelope.parent_span_id,
            )
            ctx.envelope.headers["traceparent"] = traceparent

            # Also inject into metadata for non-HTTP protocols
            ctx.envelope.metadata["trace_id"] = ctx.envelope.trace_id
            ctx.envelope.metadata["span_id"] = ctx.envelope.span_id
            if ctx.envelope.parent_span_id:
                ctx.envelope.metadata["parent_span_id"] = ctx.envelope.parent_span_id

        return ctx

