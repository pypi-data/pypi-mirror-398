"""HTTP protocol ↔ Envelope conversion logic (shared for inbound and outbound)."""

from typing import Any

from hexswitch.shared.envelope import Envelope
from hexswitch.shared.helpers import parse_request_body
from hexswitch.shared.observability.trace_context import (
    extract_trace_context_from_headers,
    inject_trace_context_to_headers,
)


class HttpEnvelope:
    """HTTP ↔ Envelope conversion logic for inbound and outbound adapters."""

    def request_to_envelope(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        query_params: dict[str, Any],
        body: bytes | None,
        path_params: dict[str, str] | None = None,
    ) -> Envelope:
        """Convert HTTP request to Envelope.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: Request path.
            headers: HTTP headers.
            query_params: Query parameters (already parsed).
            body: Request body as bytes.
            path_params: Path parameters (e.g., from route matching).

        Returns:
            Request envelope.
        """
        # Parse body
        body_dict = parse_request_body(body.decode("utf-8") if body else None)

        # Extract HTTP-specific metadata (cookies, sessions, etc.)
        metadata: dict[str, Any] = {}

        # Parse cookies from Cookie header
        if "Cookie" in headers:
            cookies = {}
            for cookie in headers["Cookie"].split(";"):
                if "=" in cookie:
                    key, value = cookie.strip().split("=", 1)
                    cookies[key] = value
            if cookies:
                metadata["cookies"] = cookies

        # Extract session ID if present
        if "X-Session-ID" in headers:
            metadata["session_id"] = headers["X-Session-ID"]

        # Extract trace context from headers
        trace_context = extract_trace_context_from_headers(headers)

        return Envelope(
            path=path,
            method=method,
            path_params=path_params or {},
            query_params=query_params,
            headers=headers,
            body=body_dict,
            metadata=metadata,
            trace_id=trace_context["trace_id"],
            span_id=trace_context["span_id"],
            parent_span_id=trace_context["parent_span_id"],
        )

    def envelope_to_response(self, envelope: Envelope) -> tuple[int, dict[str, Any], dict[str, str]]:
        """Convert Envelope to HTTP response.

        Args:
            envelope: Response envelope.

        Returns:
            Tuple of (status_code, data, headers).
        """
        status_code = envelope.status_code

        # Prepare response data
        if envelope.error_message:
            data = {"error": envelope.error_message}
        elif envelope.data:
            data = envelope.data
        else:
            data = {}

        # Build response headers
        headers: dict[str, str] = {}

        # Set cookies from metadata
        if "cookies" in envelope.metadata:
            cookies = envelope.metadata["cookies"]
            if isinstance(cookies, dict):
                # Convert to Set-Cookie headers
                cookie_strings = [f"{name}={value}; Path=/" for name, value in cookies.items()]
                if cookie_strings:
                    headers["Set-Cookie"] = ", ".join(cookie_strings)

        # Set session ID if present
        if "session_id" in envelope.metadata:
            headers["X-Session-ID"] = str(envelope.metadata["session_id"])

        # Inject trace context into response headers
        if envelope.trace_id or envelope.span_id:
            inject_trace_context_to_headers(
                headers,
                trace_id=envelope.trace_id,
                span_id=envelope.span_id,
                parent_span_id=envelope.parent_span_id,
                header_format="hexswitch",
            )

        # Copy other headers from envelope
        headers.update(envelope.headers)

        return status_code, data, headers

    def envelope_to_request(self, envelope: Envelope, base_url: str = "") -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Convert Envelope to HTTP request.

        Args:
            envelope: Request envelope.
            base_url: Base URL to prepend to path.

        Returns:
            Tuple of (method, url, headers, body_dict).
        """
        method = envelope.method or "GET"
        url = f"{base_url}{envelope.path}" if base_url else envelope.path

        # Build request headers
        headers = envelope.headers.copy()

        # Add cookies from metadata
        if "cookies" in envelope.metadata:
            cookies = envelope.metadata["cookies"]
            if isinstance(cookies, dict):
                cookie_string = "; ".join([f"{name}={value}" for name, value in cookies.items()])
                headers["Cookie"] = cookie_string

        # Add session ID if present
        if "session_id" in envelope.metadata:
            headers["X-Session-ID"] = str(envelope.metadata["session_id"])

        # Inject trace context into request headers
        if envelope.trace_id or envelope.span_id:
            inject_trace_context_to_headers(
                headers,
                trace_id=envelope.trace_id,
                span_id=envelope.span_id,
                parent_span_id=envelope.parent_span_id,
                header_format="hexswitch",
            )

        body = envelope.body

        return method, url, headers, body

    def response_to_envelope(
        self,
        status_code: int,
        data: dict[str, Any],
        headers: dict[str, str],
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert HTTP response to Envelope.

        Args:
            status_code: HTTP status code.
            data: Response data.
            headers: Response headers.
            original_envelope: Original request envelope (for preserving path/method).

        Returns:
            Response envelope.
        """
        # Extract metadata from response headers
        metadata: dict[str, Any] = {}

        # Parse Set-Cookie headers
        if "Set-Cookie" in headers:
            cookies = {}
            for cookie_header in headers["Set-Cookie"].split(","):
                if "=" in cookie_header:
                    key_value = cookie_header.strip().split(";")[0]
                    if "=" in key_value:
                        key, value = key_value.split("=", 1)
                        cookies[key] = value
            if cookies:
                metadata["cookies"] = cookies

        # Extract session ID if present
        if "X-Session-ID" in headers:
            metadata["session_id"] = headers["X-Session-ID"]

        # Extract trace context from response headers
        trace_context = extract_trace_context_from_headers(headers)

        # Determine if this is an error response
        if status_code >= 400:
            error_message = data.get("error", f"HTTP {status_code}") if isinstance(data, dict) else str(data)
            return Envelope(
                path=original_envelope.path if original_envelope else "",
                method=original_envelope.method if original_envelope else None,
                status_code=status_code,
                error_message=error_message,
                headers=headers,
                metadata=metadata,
                trace_id=trace_context["trace_id"] or (original_envelope.trace_id if original_envelope else None),
                span_id=trace_context["span_id"] or (original_envelope.span_id if original_envelope else None),
                parent_span_id=trace_context["parent_span_id"] or (original_envelope.parent_span_id if original_envelope else None),
            )
        else:
            return Envelope(
                path=original_envelope.path if original_envelope else "",
                method=original_envelope.method if original_envelope else None,
                status_code=status_code,
                data=data,
                headers=headers,
                metadata=metadata,
                trace_id=trace_context["trace_id"] or (original_envelope.trace_id if original_envelope else None),
                span_id=trace_context["span_id"] or (original_envelope.span_id if original_envelope else None),
                parent_span_id=trace_context["parent_span_id"] or (original_envelope.parent_span_id if original_envelope else None),
            )

