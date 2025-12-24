"""Tracing system for HexSwitch using OpenTelemetry."""

import logging
import sys
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace import (
    TracerProvider as SDKTracerProvider,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import (
    Span as OTelSpan,
)
from opentelemetry.trace import (
    TracerProvider,
)

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry TracerProvider
_tracer_provider: TracerProvider | None = None


class SafeConsoleSpanExporter(SpanExporter):
    """Console span exporter that handles closed file errors gracefully."""

    def __init__(self, out=None):
        """Initialize safe console exporter.

        Args:
            out: Output stream (default: sys.stdout).
        """
        self._exporter = ConsoleSpanExporter(out=out or sys.stdout)

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        """Export spans with error handling.

        Args:
            spans: List of spans to export.

        Returns:
            Export result.
        """
        try:
            return self._exporter.export(spans)
        except (ValueError, OSError) as e:
            if "closed file" in str(e).lower() or "I/O operation on closed file" in str(e):
                return SpanExportResult.SUCCESS
            raise

    def shutdown(self) -> None:
        """Shutdown exporter."""
        try:
            self._exporter.shutdown()
        except Exception:
            pass


def _get_tracer_provider() -> TracerProvider:
    """Get or create global tracer provider.

    Returns:
        Global TracerProvider instance.
    """
    global _tracer_provider
    if _tracer_provider is None:
        _tracer_provider = SDKTracerProvider(
            resource=Resource.create({"service.name": "hexswitch"})
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(SafeConsoleSpanExporter(out=sys.stdout)))
        trace.set_tracer_provider(_tracer_provider)
    return _tracer_provider


class Span:
    """Wrapper around OpenTelemetry Span for compatibility."""

    def __init__(self, otel_span: OTelSpan):
        """Initialize span wrapper.

        Args:
            otel_span: OpenTelemetry span instance.
        """
        self._span = otel_span
        self.name = otel_span.name
        # Extract trace context
        context = otel_span.get_span_context()
        self.trace_id = format(context.trace_id, "032x")
        self.span_id = format(context.span_id, "016x")
        self._parent_id: str | None = None

    @property
    def parent_id(self) -> str | None:
        """Get parent span ID."""
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value: str | None) -> None:
        """Set parent span ID."""
        self._parent_id = value

    def start(self) -> None:
        """Start the span (OpenTelemetry spans start automatically)."""
        # OpenTelemetry spans start automatically, no action needed

    def finish(self) -> None:
        """Finish the span."""
        self._span.end()

    def add_tag(self, key: str, value: str) -> None:
        """Add a tag to the span.

        Args:
            key: Tag key.
            value: Tag value.
        """
        self._span.set_attribute(key, value)

    def add_log(self, message: str, fields: dict[str, Any] | None = None) -> None:
        """Add a log entry to the span.

        Args:
            message: Log message.
            fields: Optional log fields.
        """
        if fields:
            for key, val in fields.items():
                self._span.set_attribute(f"log.{key}", str(val))
        self._span.add_event(message, attributes=fields or {})

    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary.

        Returns:
            Span as dictionary.
        """
        self._span.get_span_context()
        attributes = dict(self._span.attributes) if self._span.attributes else {}
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "tags": attributes,
            "start_time": None,  # OpenTelemetry handles this internally
            "end_time": None,
            "duration": None,
            "logs": [],  # Events are handled differently in OTel
        }


class Tracer:
    """Wrapper around OpenTelemetry Tracer for compatibility."""

    def __init__(self, service_name: str):
        """Initialize tracer.

        Args:
            service_name: Name of the service.
        """
        self.service_name = service_name
        provider = _get_tracer_provider()
        self._tracer = provider.get_tracer(service_name)
        self._spans: list[Span] = []

    def start_span(
        self,
        name: str,
        parent: Span | None = None,
        tags: dict[str, str] | None = None,
    ) -> Span:
        """Start a new span.

        Args:
            name: Span name.
            parent: Parent span (optional).
            tags: Initial tags.

        Returns:
            New span.
        """
        # Get parent context if available
        if parent:
            parent_context = trace.set_span_in_context(parent._span)
            otel_span = self._tracer.start_span(name, context=parent_context)
        else:
            otel_span = self._tracer.start_span(name)

        # Set initial tags
        if tags:
            for key, value in tags.items():
                otel_span.set_attribute(key, value)

        # Create wrapper
        span = Span(otel_span)
        if parent:
            span.parent_id = parent.span_id

        self._spans.append(span)
        return span

    def get_spans(self) -> list[Span]:
        """Get all spans.

        Returns:
            List of spans.
        """
        return self._spans.copy()

    def clear(self) -> None:
        """Clear all spans."""
        self._spans.clear()


_global_tracer: Tracer | None = None


def create_tracer(service_name: str) -> Tracer:
    """Create a new tracer instance.

    Args:
        service_name: Name of the service.

    Returns:
        New Tracer instance.
    """
    return Tracer(service_name)


def get_global_tracer() -> Tracer:
    """Get or create global tracer.

    Returns:
        Global Tracer instance.
    """
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer("hexswitch")
    return _global_tracer


def start_span(
    name: str,
    parent: Span | None = None,
    tags: dict[str, str] | None = None,
) -> Span:
    """Start a new span using global tracer.

    Args:
        name: Span name.
        parent: Parent span (optional).
        tags: Initial tags.

    Returns:
        New span.
    """
    tracer = get_global_tracer()
    # Get parent context if available
    parent_context = None
    if parent:
        parent_context = trace.set_span_in_context(parent._span)

    # Start span with context
    if parent_context:
        otel_span = tracer._tracer.start_span(name, context=parent_context)
    else:
        otel_span = tracer._tracer.start_span(name)

    # Set initial tags
    if tags:
        for key, value in tags.items():
            otel_span.set_attribute(key, value)

    # Create wrapper
    span = Span(otel_span)
    if parent:
        span.parent_id = parent.span_id

    # Set as current span in context
    trace.set_span_in_context(otel_span)
    trace.use_span(otel_span, end_on_exit=False).__enter__()

    tracer._spans.append(span)
    return span


def get_current_span() -> Span | None:
    """Get current span from context.

    Returns:
        Current span or None.
    """
    current = trace.get_current_span()
    # Check if span is valid (has valid span context)
    if current:
        span_context = current.get_span_context()
        if span_context.is_valid:
            return Span(current)
    return None
