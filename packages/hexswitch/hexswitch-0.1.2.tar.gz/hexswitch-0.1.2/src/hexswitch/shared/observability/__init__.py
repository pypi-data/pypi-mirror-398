"""Observability - tracing, metrics, and trace context."""

from hexswitch.shared.observability.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    create_metrics_collector,
    get_global_metrics_collector,
)
from hexswitch.shared.observability.trace_context import (
    create_trace_context,
    extract_trace_context_from_grpc_metadata,
    extract_trace_context_from_headers,
    get_trace_context_from_current_span,
    inject_trace_context_to_grpc_metadata,
    inject_trace_context_to_headers,
)
from hexswitch.shared.observability.tracing import (
    Span,
    Tracer,
    create_tracer,
    get_current_span,
    get_global_tracer,
    start_span,
)

__all__ = [
    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsCollector",
    "create_metrics_collector",
    "get_global_metrics_collector",
    # Tracing
    "Span",
    "Tracer",
    "create_tracer",
    "get_current_span",
    "get_global_tracer",
    "start_span",
    # Trace Context
    "create_trace_context",
    "extract_trace_context_from_grpc_metadata",
    "extract_trace_context_from_headers",
    "get_trace_context_from_current_span",
    "inject_trace_context_to_grpc_metadata",
    "inject_trace_context_to_headers",
]
