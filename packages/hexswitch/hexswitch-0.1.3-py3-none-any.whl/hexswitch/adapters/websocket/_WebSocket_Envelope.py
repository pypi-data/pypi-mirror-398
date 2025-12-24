"""WebSocket protocol ↔ Envelope conversion logic (shared for inbound and outbound)."""

import json
from typing import Any

from hexswitch.shared.envelope import Envelope


class WebSocketEnvelope:
    """WebSocket ↔ Envelope conversion logic for inbound and outbound adapters."""

    def request_to_envelope(
        self,
        message: str | bytes,
        path: str,
        remote_address: str | None = None,
        websocket_id: int | None = None,
    ) -> Envelope:
        """Convert WebSocket message to Envelope (alias for message_to_envelope).

        This method implements the abstract request_to_envelope method
        by delegating to message_to_envelope.
        """
        return self.message_to_envelope(message, path, remote_address, websocket_id)

    def message_to_envelope(
        self,
        message: str | bytes,
        path: str,
        remote_address: str | None = None,
        websocket_id: int | None = None,
    ) -> Envelope:
        """Convert WebSocket message to Envelope.

        Args:
            message: WebSocket message (string or bytes).
            path: WebSocket path.
            remote_address: Remote address.
            websocket_id: WebSocket connection ID.

        Returns:
            Request envelope.
        """
        # Try to parse as JSON, fallback to raw message
        try:
            if isinstance(message, bytes):
                message_str = message.decode("utf-8")
            else:
                message_str = str(message)

            try:
                message_data = json.loads(message_str)
            except (json.JSONDecodeError, TypeError):
                message_data = {"raw": message_str}
        except Exception:
            message_data = {"raw": str(message)}

        metadata: dict[str, Any] = {
            "raw_message": str(message),
        }

        if remote_address:
            metadata["remote_address"] = remote_address
        if websocket_id:
            metadata["websocket_id"] = websocket_id

        return Envelope(
            path=path,
            method=None,  # WebSocket doesn't use HTTP methods
            path_params={},
            query_params={},
            headers={},
            body=message_data if isinstance(message_data, dict) else None,
            metadata=metadata,
        )

    def envelope_to_response(self, envelope: Envelope) -> str:
        """Convert Envelope to WebSocket message (implements abstract method).

        This method implements the abstract envelope_to_response method
        by delegating to envelope_to_message.
        """
        return self.envelope_to_message(envelope)

    def envelope_to_message(self, envelope: Envelope) -> str:
        """Convert Envelope to WebSocket message.

        Args:
            envelope: Response envelope.

        Returns:
            WebSocket message as JSON string.
        """
        if envelope.error_message:
            return json.dumps({"error": envelope.error_message})
        elif envelope.data:
            return json.dumps(envelope.data)
        else:
            return json.dumps({})

    def envelope_to_request(self, envelope: Envelope) -> str:
        """Convert Envelope to WebSocket request message.

        Args:
            envelope: Request envelope.

        Returns:
            WebSocket message as JSON string.
        """
        if envelope.body:
            return json.dumps(envelope.body)
        else:
            return json.dumps({})

    def response_to_envelope(
        self,
        message: str | bytes,
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert WebSocket response message to Envelope (implements abstract method).

        This method implements the abstract response_to_envelope method
        by delegating to message_to_envelope_response.
        """
        return self.message_to_envelope_response(message, original_envelope)

    def message_to_envelope_response(
        self,
        message: str | bytes,
        original_envelope: Envelope | None = None,
    ) -> Envelope:
        """Convert WebSocket response message to Envelope.

        Args:
            message: WebSocket message.
            original_envelope: Original request envelope.

        Returns:
            Response envelope.
        """
        # Try to parse as JSON
        try:
            if isinstance(message, bytes):
                message_str = message.decode("utf-8")
            else:
                message_str = str(message)

            try:
                message_data = json.loads(message_str)
            except (json.JSONDecodeError, TypeError):
                message_data = {"raw": message_str}
        except Exception:
            message_data = {"raw": str(message)}

        # Check if it's an error
        if isinstance(message_data, dict) and "error" in message_data:
            return Envelope(
                path=original_envelope.path if original_envelope else "",
                method=original_envelope.method if original_envelope else None,
                status_code=500,
                error_message=message_data["error"],
                metadata=original_envelope.metadata.copy() if original_envelope else {},
            )
        else:
            return Envelope(
                path=original_envelope.path if original_envelope else "",
                method=original_envelope.method if original_envelope else None,
                status_code=200,
                data=message_data if isinstance(message_data, dict) else None,
                metadata=original_envelope.metadata.copy() if original_envelope else {},
            )

