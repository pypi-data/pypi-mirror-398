"""Observability middleware for spans, metrics, and structured logging."""

from __future__ import annotations

import logging
from typing import Any, Callable

from hexswitch.pipeline.pipeline import PipelineContext
from hexswitch.shared.observability import get_global_metrics_collector, get_global_tracer, start_span

logger = logging.getLogger(__name__)


class ObservabilityMiddleware:
    """Middleware that adds observability (spans, metrics, logs)."""

    def __init__(self):
        """Initialize observability middleware."""
        self._tracer = get_global_tracer()
        self._metrics = get_global_metrics_collector()

    async def __call__(
        self, ctx: PipelineContext, next: Callable[[PipelineContext], "Any"]
    ) -> PipelineContext:
        """Add observability (spans, metrics, logs).

        Args:
            ctx: Pipeline context
            next: Next middleware in chain

        Returns:
            Updated context
        """
        # Extract trace context from envelope
        original_span_id = ctx.envelope.span_id
        parent_span_id = ctx.envelope.parent_span_id

        # Create span name
        span_name = f"{ctx.stage}.{ctx.port_name or 'unknown'}"

        # Start span with trace context
        parent_span = None
        if parent_span_id:
            # Try to get parent span from context
            try:
                from hexswitch.shared.observability.tracing import get_current_span

                current_span = get_current_span()
                if current_span and current_span.span_id == parent_span_id:
                    parent_span = current_span
            except Exception:
                pass

        # Start span (trace_id is handled automatically by the tracer)
        span = start_span(
            span_name,
            parent=parent_span,
            tags={"port": ctx.port_name or "unknown", "stage": ctx.stage},
        )
        ctx.metadata["span"] = span

        # Update envelope with new span context
        ctx.envelope.trace_id = span.trace_id
        ctx.envelope.span_id = span.span_id
        if original_span_id:
            ctx.envelope.parent_span_id = original_span_id

        # Record start metrics
        self._record_start_metrics(ctx)

        try:
            # Call next middleware
            ctx = await next(ctx)

            # Record success metrics
            self._record_success_metrics(ctx)

            # Log structured log
            self._log(ctx, "success")

            return ctx

        except Exception as e:
            # Record error metrics
            self._record_error_metrics(ctx, e)

            # Log error
            self._log(ctx, "error", error=str(e))

            raise

        finally:
            # Finish span
            span.finish()

    def _record_start_metrics(self, ctx: PipelineContext) -> None:
        """Record start metrics.

        Args:
            ctx: Pipeline context
        """
        counter = self._metrics.counter(
            "pipeline_stage_starts_total",
            labels={"stage": ctx.stage, "port": ctx.port_name or "unknown"},
        )
        counter.inc()

    def _record_success_metrics(self, ctx: PipelineContext) -> None:
        """Record success metrics.

        Args:
            ctx: Pipeline context
        """
        counter = self._metrics.counter(
            "pipeline_stage_success_total",
            labels={"stage": ctx.stage, "port": ctx.port_name or "unknown"},
        )
        counter.inc()

        # Record duration if available
        if "duration" in ctx.metadata:
            histogram = self._metrics.histogram(
                "pipeline_stage_duration_seconds",
                labels={"stage": ctx.stage},
            )
            histogram.observe(ctx.metadata["duration"])

    def _record_error_metrics(self, ctx: PipelineContext, error: Exception) -> None:
        """Record error metrics.

        Args:
            ctx: Pipeline context
            error: Exception that occurred
        """
        counter = self._metrics.counter(
            "pipeline_stage_errors_total",
            labels={
                "stage": ctx.stage,
                "port": ctx.port_name or "unknown",
                "error_type": type(error).__name__,
            },
        )
        counter.inc()

    def _log(self, ctx: PipelineContext, level: str, error: str | None = None) -> None:
        """Log structured log entry.

        Args:
            ctx: Pipeline context
            level: Log level (success, error)
            error: Error message if level is error
        """
        log_data = {
            "stage": ctx.stage,
            "port": ctx.port_name,
            "path": ctx.envelope.path,
            "method": ctx.envelope.method,
            "status_code": ctx.envelope.status_code,
        }

        # Add trace context if available
        if ctx.envelope.trace_id:
            log_data["trace_id"] = ctx.envelope.trace_id
        if ctx.envelope.span_id:
            log_data["span_id"] = ctx.envelope.span_id

        if error:
            log_data["error"] = error

        if level == "error":
            logger.error(f"Pipeline {ctx.stage} error", extra=log_data)
        else:
            logger.info(f"Pipeline {ctx.stage} success", extra=log_data)

