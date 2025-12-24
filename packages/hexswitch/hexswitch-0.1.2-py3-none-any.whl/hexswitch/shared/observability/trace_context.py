"""Trace context propagation utilities using OpenTelemetry.

This module provides helpers for extracting and propagating trace context
across protocol boundaries (HTTP, gRPC, WebSocket, etc.) using OpenTelemetry.

Supports multiple trace context formats:
- W3C Trace Context (traceparent, tracestate) - via OpenTelemetry
- B3 (X-B3-TraceId, X-B3-SpanId, X-B3-ParentSpanId) - manual fallback
- Custom HexSwitch format (X-Trace-Id, X-Span-Id, X-Parent-Span-Id) - manual fallback
"""

from typing import Any
import uuid

from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from hexswitch.shared.observability.tracing import Span, get_current_span

# Standard trace context header names
W3C_TRACEPARENT = "traceparent"
W3C_TRACESTATE = "tracestate"
B3_TRACE_ID = "X-B3-TraceId"
B3_SPAN_ID = "X-B3-SpanId"
B3_PARENT_SPAN_ID = "X-B3-ParentSpanId"
B3_SAMPLED = "X-B3-Sampled"
HEXSWITCH_TRACE_ID = "X-Trace-Id"
HEXSWITCH_SPAN_ID = "X-Span-Id"
HEXSWITCH_PARENT_SPAN_ID = "X-Parent-Span-Id"


def extract_trace_context_from_headers(headers: dict[str, str]) -> dict[str, str | None]:
    """Extract trace context from HTTP headers using OpenTelemetry.

    Supports multiple formats:
    - W3C Trace Context (traceparent) - via OpenTelemetry
    - B3 (X-B3-*) - manual fallback
    - HexSwitch (X-Trace-Id, X-Span-Id, X-Parent-Span-Id) - manual fallback

    Args:
        headers: HTTP headers dictionary.

    Returns:
        Dictionary with trace_id, span_id, parent_span_id (or None if not found).
    """
    # Try W3C Trace Context format first using OpenTelemetry
    # Normalize headers to lowercase for case-insensitive matching
    normalized_headers = {k.lower(): v for k, v in headers.items()}
    propagator = TraceContextTextMapPropagator()
    try:
        # OpenTelemetry expects lowercase header names
        context = propagator.extract(carrier=normalized_headers)
        span_context = trace.get_current_span(context).get_span_context()

        if span_context.is_valid:
            return {
                "trace_id": format(span_context.trace_id, "032x"),
                "span_id": format(span_context.span_id, "016x"),
                "parent_span_id": None,  # OTel handles this internally
            }
    except Exception:
        pass  # Fall through to manual parsing

    # Try B3 format (manual parsing)
    if B3_TRACE_ID in headers:
        return {
            "trace_id": headers[B3_TRACE_ID],
            "span_id": headers.get(B3_SPAN_ID),
            "parent_span_id": headers.get(B3_PARENT_SPAN_ID),
        }

    # Try HexSwitch format (fallback)
    if HEXSWITCH_TRACE_ID in headers:
        return {
            "trace_id": headers.get(HEXSWITCH_TRACE_ID),
            "span_id": headers.get(HEXSWITCH_SPAN_ID),
            "parent_span_id": headers.get(HEXSWITCH_PARENT_SPAN_ID),
        }

    return {
        "trace_id": None,
        "span_id": None,
        "parent_span_id": None,
    }


def inject_trace_context_to_headers(
    headers: dict[str, str],
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
    header_format: str = "w3c",  # "w3c", "b3", or "hexswitch"
) -> dict[str, str]:
    """Inject trace context into HTTP headers using OpenTelemetry.

    Args:
        headers: HTTP headers dictionary (will be modified).
        trace_id: Trace ID.
        span_id: Current span ID.
        parent_span_id: Parent span ID.
        header_format: Header format ("w3c", "b3", or "hexswitch").

    Returns:
        Updated headers dictionary.
    """
    if header_format == "w3c":
        # Use OpenTelemetry propagator for W3C format
        try:
            propagator = TraceContextTextMapPropagator()
            propagator.inject(carrier=headers)
            return headers
        except Exception:
            # Fallback to manual if OpenTelemetry context not available
            pass

    # Manual injection for B3 or HexSwitch format
    if not trace_id:
        return headers

    if header_format == "b3":
        # B3 format
        headers[B3_TRACE_ID] = trace_id
        if span_id:
            headers[B3_SPAN_ID] = span_id
        if parent_span_id:
            headers[B3_PARENT_SPAN_ID] = parent_span_id
        headers[B3_SAMPLED] = "1"
    else:
        # HexSwitch format (default fallback)
        headers[HEXSWITCH_TRACE_ID] = trace_id
        if span_id:
            headers[HEXSWITCH_SPAN_ID] = span_id
        if parent_span_id:
            headers[HEXSWITCH_PARENT_SPAN_ID] = parent_span_id

    return headers


def extract_trace_context_from_grpc_metadata(metadata: dict[str, Any]) -> dict[str, str | None]:
    """Extract trace context from gRPC metadata using OpenTelemetry.

    Args:
        metadata: gRPC metadata dictionary.

    Returns:
        Dictionary with trace_id, span_id, parent_span_id (or None if not found).
    """
    # gRPC metadata is typically a list of tuples, but we handle dict format too
    if isinstance(metadata, dict):
        return extract_trace_context_from_headers(metadata)

    # Convert list of tuples to dict
    headers = {}
    if isinstance(metadata, list):
        for key, value in metadata:
            headers[key.lower()] = str(value)

    return extract_trace_context_from_headers(headers)


def inject_trace_context_to_grpc_metadata(
    metadata: list[tuple[str, str]],
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
) -> list[tuple[str, str]]:
    """Inject trace context into gRPC metadata using OpenTelemetry.

    Args:
        metadata: gRPC metadata list of tuples (will be modified).
        trace_id: Trace ID.
        span_id: Current span ID.
        parent_span_id: Parent span ID.

    Returns:
        Updated metadata list.
    """
    # Convert to dict for propagation
    headers = dict(metadata)

    # Try OpenTelemetry propagation first
    try:
        propagator = TraceContextTextMapPropagator()
        propagator.inject(carrier=headers)
        # Convert back to list
        return list(headers.items())
    except Exception:
        pass

    # Fallback to HexSwitch format for gRPC
    if trace_id:
        headers[HEXSWITCH_TRACE_ID.lower()] = trace_id
        if span_id:
            headers[HEXSWITCH_SPAN_ID.lower()] = span_id
        if parent_span_id:
            headers[HEXSWITCH_PARENT_SPAN_ID.lower()] = parent_span_id

    return list(headers.items())


def get_trace_context_from_current_span() -> dict[str, str | None]:
    """Get trace context from current span using OpenTelemetry.

    Returns:
        Dictionary with trace_id, span_id, parent_span_id (or None if no current span).
    """
    current_span = get_current_span()
    if not current_span:
        return {
            "trace_id": None,
            "span_id": None,
            "parent_span_id": None,
        }

    return {
        "trace_id": current_span.trace_id,
        "span_id": current_span.span_id,
        "parent_span_id": current_span.parent_id,
    }


def create_trace_context(
    trace_id: str | None = None,
    parent_span: Span | None = None,
) -> dict[str, str | None]:
    """Create new trace context.

    Args:
        trace_id: Trace ID (uses parent's trace_id if parent_span provided).
        parent_span: Parent span (for creating child span context).

    Returns:
        Dictionary with trace_id, span_id, parent_span_id.
    """
    if parent_span:
        trace_id = parent_span.trace_id
        parent_span_id = parent_span.span_id
    else:
        trace_id = trace_id or str(uuid.uuid4())
        parent_span_id = None

    span_id = str(uuid.uuid4())

    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
    }
