"""Envelope base class with integrated observability support."""

from dataclasses import dataclass, field
from typing import Any
import uuid

from hexswitch.shared.observability.tracing import Span, get_current_span, start_span


@dataclass
class Envelope:
    """Unified request/response structure for all protocols with integrated observability.

    The Envelope standardizes communication between adapters, ports, and handlers
    by providing a common format that works across all protocols (HTTP, gRPC, WebSocket, etc.).

    Protocol-specific data (sessions, cookies, metadata, etc.) is managed by adapters
    and integrated into the Envelope.

    Observability (tracing, metrics) is integrated directly into the Envelope class,
    allowing automatic span creation and trace context propagation.

    Attributes:
        path: Request path (e.g., "/orders", "/orders/:id")
        method: HTTP method (e.g., "GET", "POST", "PUT", "DELETE") or None for non-HTTP protocols
        path_params: Path parameters extracted from route (e.g., {"id": "123"})
        query_params: Query parameters from URL (e.g., {"page": "1", "limit": "10"})
        headers: Request headers (e.g., {"Authorization": "Bearer token"})
        body: Request body as dictionary (parsed JSON, form data, etc.)
        status_code: HTTP status code for response (default: 200)
        data: Response data as dictionary (for successful responses)
        error_message: Error message (for error responses)
        metadata: Protocol-agnostic metadata (e.g., session_id, cookies, gRPC metadata as dict)
        trace_id: Trace ID for distributed tracing (automatically set by adapters)
        span_id: Current span ID (automatically set by adapters)
        parent_span_id: Parent span ID (for span hierarchy, automatically set by adapters)
    """

    # Request fields
    path: str
    method: str | None = None
    path_params: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None

    # Response fields
    status_code: int = 200
    data: dict[str, Any] | None = None
    error_message: str | None = None

    # Protocol-agnostic metadata (optional, managed by adapter)
    # Adapters can store protocol-specific data here (e.g., session_id, cookies, gRPC metadata)
    # but should convert it to protocol-agnostic format
    metadata: dict[str, Any] = field(default_factory=dict)

    # Tracing context (optional, for distributed tracing)
    # Automatically extracted/propagated by adapters
    trace_id: str | None = None  # Trace ID for distributed tracing
    span_id: str | None = None  # Current span ID
    parent_span_id: str | None = None  # Parent span ID (for span hierarchy)

    # Internal observability state
    _span: Span | None = field(default=None, init=False, repr=False)

    @classmethod
    def success(cls, data: dict[str, Any], status_code: int = 200) -> "Envelope":
        """Factory method for successful responses.

        Args:
            data: Response data dictionary
            status_code: HTTP status code (default: 200)

        Returns:
            Envelope instance with success response

        Example:
            >>> envelope = Envelope.success({"order_id": "123", "status": "created"})
            >>> envelope.status_code
            200
            >>> envelope.data
            {'order_id': '123', 'status': 'created'}
        """
        return cls(path="", status_code=status_code, data=data)

    @classmethod
    def error(cls, status_code: int, error: str) -> "Envelope":
        """Factory method for error responses.

        Args:
            status_code: HTTP status code (e.g., 400, 404, 500)
            error: Error message

        Returns:
            Envelope instance with error response

        Example:
            >>> envelope = Envelope.error(400, "customer_id is required")
            >>> envelope.status_code
            400
            >>> envelope.error_message
            'customer_id is required'
        """
        return cls(path="", status_code=status_code, error_message=error)

    # Observability methods

    def start_span(self, name: str | None = None, tags: dict[str, str] | None = None) -> Span:
        """DEPRECATED: Use Runtime.dispatch() instead.

        This method is deprecated and will be removed in a future version.
        Spans are now created automatically by the pipeline middleware.

        Start a new span for this envelope.

        If trace_id is already set, creates a child span. Otherwise, creates a new trace.
        The span is automatically associated with this envelope.

        Args:
            name: Span name (defaults to path or "envelope")
            tags: Optional span tags

        Returns:
            Started span instance
        """
        import warnings

        warnings.warn(
            "Envelope.start_span() is deprecated. "
            "Use Runtime.dispatch() instead. Spans are created automatically by the pipeline middleware.",
            DeprecationWarning,
            stacklevel=2,
        )
        span_name = name or self.path or "envelope"

        # Get parent span if trace context exists
        parent_span = None
        if self.trace_id:
            # Try to get current span from context
            current_span = get_current_span()
            if current_span and current_span.trace_id == self.trace_id:
                parent_span = current_span
            elif self.parent_span_id:
                # Create a parent span reference (simplified)
                # In a real implementation, you'd look up the parent span
                pass

        # Create tags from envelope data
        span_tags = tags or {}
        if self.path:
            span_tags["envelope.path"] = self.path
        if self.method:
            span_tags["envelope.method"] = self.method
        if self.status_code:
            span_tags["envelope.status_code"] = str(self.status_code)

        # Start span
        span = start_span(span_name, parent=parent_span, tags=span_tags)

        # Update envelope trace context from span
        self.trace_id = span.trace_id
        self.span_id = span.span_id
        if parent_span:
            self.parent_span_id = parent_span.span_id

        # Store span reference
        self._span = span

        return span

    def finish_span(self) -> None:
        """DEPRECATED: Use Runtime.dispatch() instead.

        This method is deprecated and will be removed in a future version.
        Spans are now finished automatically by the pipeline middleware.

        Finish the associated span for this envelope.

        Adds envelope-specific tags and logs before finishing.
        """
        import warnings

        warnings.warn(
            "Envelope.finish_span() is deprecated. "
            "Use Runtime.dispatch() instead. Spans are finished automatically by the pipeline middleware.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self._span:
            return

        # Add final tags
        if self.error_message:
            self._span.add_tag("error", "true")
            self._span.add_tag("error.message", self.error_message)
        else:
            self._span.add_tag("success", "true")

        # Add log entry
        log_fields: dict[str, Any] = {
            "status_code": self.status_code,
        }
        if self.data:
            log_fields["has_data"] = True
        if self.error_message:
            log_fields["error"] = self.error_message

        self._span.add_log(
            f"Envelope completed: {self.path}",
            fields=log_fields,
        )

        # Finish span
        self._span.finish()

    def get_span(self) -> Span | None:
        """DEPRECATED: Use Runtime.dispatch() instead.

        This method is deprecated and will be removed in a future version.
        Spans are now managed by the pipeline middleware.

        Get the associated span for this envelope.

        Returns:
            Span instance or None if no span is associated
        """
        import warnings

        warnings.warn(
            "Envelope.get_span() is deprecated. "
            "Use Runtime.dispatch() instead. Spans are managed by the pipeline middleware.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._span

    def has_trace_context(self) -> bool:
        """Check if this envelope has trace context.

        Returns:
            True if trace_id is set, False otherwise
        """
        return self.trace_id is not None

    def create_child_context(self) -> dict[str, str]:
        """Create trace context for a child span.

        Returns:
            Dictionary with trace_id, span_id (new), parent_span_id (current span_id)
        """
        if not self.trace_id:
            # Create new trace if none exists
            self.trace_id = str(uuid.uuid4())
            self.span_id = str(uuid.uuid4())
            self.parent_span_id = None
        else:
            # Create child context
            self.parent_span_id = self.span_id
            self.span_id = str(uuid.uuid4())

        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id or "",
        }

    def __enter__(self) -> "Envelope":
        """Context manager entry - automatically starts span."""
        span_name = self.path or "envelope"

        # Get parent span if trace context exists
        parent_span = None
        if self.trace_id:
            # Try to get current span from context
            current_span = get_current_span()
            if current_span and current_span.trace_id == self.trace_id:
                parent_span = current_span
            elif self.parent_span_id:
                # Create a parent span reference (simplified)
                # In a real implementation, you'd look up the parent span
                pass

        # Create tags from envelope data
        span_tags: dict[str, str] = {}
        if self.path:
            span_tags["envelope.path"] = self.path
        if self.method:
            span_tags["envelope.method"] = self.method
        if self.status_code:
            span_tags["envelope.status_code"] = str(self.status_code)

        # Start span directly (without using deprecated method)
        span = start_span(span_name, parent=parent_span, tags=span_tags)

        # Update envelope trace context from span
        self.trace_id = span.trace_id
        self.span_id = span.span_id
        if parent_span:
            self.parent_span_id = parent_span.span_id

        # Store span reference
        self._span = span

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - automatically finishes span."""
        if not self._span:
            return

        # Add final tags
        if exc_type:
            self._span.add_tag("error", "true")
            self._span.add_log(f"Exception: {exc_type.__name__}", fields={"exception": str(exc_val)})
        elif self.error_message:
            self._span.add_tag("error", "true")
            self._span.add_tag("error.message", self.error_message)
        else:
            self._span.add_tag("success", "true")

        # Add log entry
        log_fields: dict[str, Any] = {
            "status_code": self.status_code,
        }
        if self.data:
            log_fields["has_data"] = True
        if self.error_message:
            log_fields["error"] = self.error_message

        self._span.add_log(
            f"Envelope completed: {self.path}",
            fields=log_fields,
        )

        # Finish span directly (without using deprecated method)
        self._span.finish()

