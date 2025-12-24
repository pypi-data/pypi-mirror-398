"""NATS protocol ↔ Envelope conversion logic."""

import json
from typing import Any

from hexswitch.shared.envelope import Envelope
from hexswitch.shared.observability.trace_context import (
    extract_trace_context_from_headers,
    inject_trace_context_to_headers,
)


class NatsEnvelope:
    """NATS ↔ Envelope conversion logic for inbound and outbound adapters."""

    def message_to_envelope(
        self,
        subject: str,
        data: bytes,
        headers: dict[str, str] | None = None,
        reply_to: str | None = None,
    ) -> Envelope:
        """Convert NATS message to Envelope.

        Args:
            subject: NATS subject.
            data: Message data as bytes.
            headers: NATS headers (optional).
            reply_to: Reply subject (for request/reply pattern).

        Returns:
            Request envelope.
        """
        # Parse message body
        try:
            body_dict = json.loads(data.decode("utf-8")) if data else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON, treat as plain text
            body_dict = {"raw": data.decode("utf-8", errors="ignore")}

        # Extract metadata
        metadata: dict[str, Any] = {
            "subject": subject,
            "reply_to": reply_to,
        }

        # Extract trace context from headers if present
        trace_context = {}
        if headers:
            trace_context = extract_trace_context_from_headers(headers)
            # Store all headers in metadata
            metadata["headers"] = headers

        # Create envelope
        envelope = Envelope(
            path=subject,  # Use subject as path
            method=None,  # NATS doesn't have HTTP methods
            path_params={},
            query_params={},
            headers=headers or {},
            body=body_dict,
            metadata=metadata,
            trace_id=trace_context.get("trace_id"),
            span_id=trace_context.get("span_id"),
            parent_span_id=trace_context.get("parent_span_id"),
        )

        return envelope

    def envelope_to_message(
        self,
        envelope: Envelope,
        subject: str | None = None,
        reply_to: str | None = None,
    ) -> tuple[bytes, dict[str, str]]:
        """Convert Envelope to NATS message.

        Args:
            envelope: Response envelope.
            subject: NATS subject (if None, use envelope.path).
            reply_to: Reply subject (for request/reply pattern).

        Returns:
            Tuple of (message_data, headers).
        """
        # Convert envelope data to JSON
        message_data = json.dumps(envelope.data or {}).encode("utf-8")

        # Build headers
        headers: dict[str, str] = {}

        # Inject trace context into headers
        if envelope.trace_id:
            trace_headers = inject_trace_context_to_headers(
                {
                    "trace_id": envelope.trace_id,
                    "span_id": envelope.span_id,
                    "parent_span_id": envelope.parent_span_id,
                }
            )
            headers.update(trace_headers)

        # Add envelope metadata to headers
        if envelope.metadata:
            if "headers" in envelope.metadata:
                headers.update(envelope.metadata["headers"])

        # Add reply subject if provided
        if reply_to:
            headers["Nats-Reply-To"] = reply_to

        return (message_data, headers)

    def envelope_to_response_envelope(
        self,
        envelope: Envelope,
        original_subject: str | None = None,
    ) -> Envelope:
        """Convert Envelope (response) back to Envelope format for reply.

        This is used for request/reply pattern where we need to send
        a response envelope back.

        Args:
            envelope: Response envelope.
            original_subject: Original subject (for reply).

        Returns:
            Response envelope (same as input, but with metadata updated).
        """
        # Update metadata with reply information
        if original_subject:
            envelope.metadata = envelope.metadata or {}
            envelope.metadata["reply_subject"] = original_subject

        return envelope

