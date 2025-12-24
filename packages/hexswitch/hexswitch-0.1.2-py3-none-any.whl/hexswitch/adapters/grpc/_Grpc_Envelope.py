"""gRPC protocol ↔ Envelope conversion logic (shared for inbound and outbound)."""

from typing import Any

import grpc

from hexswitch.shared.envelope import Envelope
from hexswitch.shared.observability.trace_context import (
    extract_trace_context_from_grpc_metadata,
)


class GrpcEnvelope:
    """gRPC ↔ Envelope conversion logic for inbound and outbound adapters."""

    @staticmethod
    def request_to_envelope(
        request: Any,
        context: Any,
        service_name: str,
        method_name: str,
    ) -> Envelope:
        """Convert gRPC request to Envelope.

        Args:
            request: gRPC request object (protobuf message).
            context: gRPC context.
            service_name: Service name.
            method_name: Method name.

        Returns:
            Request envelope.
        """
        # Extract metadata from context
        metadata_dict: dict[str, Any] = {}
        metadata_list: list[tuple[str, str]] = []
        if hasattr(context, "invocation_metadata"):
            for key, value in context.invocation_metadata():
                metadata_dict[key] = value
                metadata_list.append((key, value))

        # Extract trace context from gRPC metadata
        trace_context = extract_trace_context_from_grpc_metadata(metadata_list)

        # Convert protobuf message to dict
        request_dict: dict[str, Any] = {}
        if hasattr(request, "DESCRIPTOR"):
            # Try to convert protobuf message to dict
            for field in request.DESCRIPTOR.fields:
                field_name = field.name
                field_value = getattr(request, field_name, None)
                # Convert repeated fields to list
                if field.label == field.LABEL_REPEATED:
                    request_dict[field_name] = list(field_value) if field_value else []
                else:
                    request_dict[field_name] = field_value

        return Envelope(
            path=f"/{service_name}/{method_name}",
            method=None,  # gRPC doesn't use HTTP methods
            path_params={},
            query_params={},
            headers={},
            body=request_dict if request_dict else None,
            metadata={
                "service": service_name,
                "method": method_name,
                "grpc_metadata": metadata_dict,
            },
            trace_id=trace_context["trace_id"],
            span_id=trace_context["span_id"],
            parent_span_id=trace_context["parent_span_id"],
        )

    def envelope_to_response(self, envelope: Envelope) -> dict[str, Any]:
        """Convert Envelope to gRPC response.

        Args:
            envelope: Response envelope.

        Returns:
            Response data dictionary (to be converted to protobuf message).
        """
        if envelope.error_message:
            # Error will be handled by setting context status
            return {}

        return envelope.data or {}

    def envelope_to_request(self, envelope: Envelope) -> dict[str, Any]:
        """Convert Envelope to gRPC request.

        Args:
            envelope: Request envelope.

        Returns:
            Request data dictionary (to be converted to protobuf message).
        """
        return envelope.body or {}

    @staticmethod
    def response_to_envelope(
        response: Any,
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert gRPC response to Envelope.

        Args:
            response: gRPC response object (protobuf message).
            original_envelope: Original request envelope.

        Returns:
            Response envelope.
        """
        # Convert protobuf message to dict
        response_dict: dict[str, Any] = {}
        if hasattr(response, "DESCRIPTOR"):
            for field in response.DESCRIPTOR.fields:
                field_name = field.name
                field_value = getattr(response, field_name, None)
                if field.label == field.LABEL_REPEATED:
                    response_dict[field_name] = list(field_value) if field_value else []
                else:
                    response_dict[field_name] = field_value

        return Envelope(
            path=original_envelope.path if original_envelope else "",
            method=original_envelope.method if original_envelope else None,
            status_code=200,
            data=response_dict if response_dict else None,
            metadata=original_envelope.metadata.copy() if original_envelope else {},
            trace_id=original_envelope.trace_id if original_envelope else None,
            span_id=original_envelope.span_id if original_envelope else None,
            parent_span_id=original_envelope.parent_span_id if original_envelope else None,
        )

    @staticmethod
    def error_to_envelope(
        status_code: grpc.StatusCode,
        error_message: str,
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert gRPC error to Envelope.

        Args:
            status_code: gRPC status code.
            error_message: Error message.
            original_envelope: Original request envelope.

        Returns:
            Error envelope.
        """
        # Map gRPC status codes to HTTP status codes
        http_status = 500
        if status_code == grpc.StatusCode.NOT_FOUND:
            http_status = 404
        elif status_code == grpc.StatusCode.INVALID_ARGUMENT:
            http_status = 400
        elif status_code == grpc.StatusCode.UNAUTHENTICATED:
            http_status = 401
        elif status_code == grpc.StatusCode.PERMISSION_DENIED:
            http_status = 403

        return Envelope(
            path=original_envelope.path if original_envelope else "",
            method=original_envelope.method if original_envelope else None,
            status_code=http_status,
            error_message=error_message,
            metadata=original_envelope.metadata.copy() if original_envelope else {},
            trace_id=original_envelope.trace_id if original_envelope else None,
            span_id=original_envelope.span_id if original_envelope else None,
            parent_span_id=original_envelope.parent_span_id if original_envelope else None,
        )

