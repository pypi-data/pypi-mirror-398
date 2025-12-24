"""HTTP client outbound adapter implementation."""

import json
import logging
from typing import Any

import requests

from hexswitch.adapters.base import OutboundAdapter
from hexswitch.adapters.exceptions import AdapterConnectionError
from hexswitch.adapters.http._Http_Envelope import HttpEnvelope
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


class HttpAdapterClient(OutboundAdapter):
    """HTTP client outbound adapter for making HTTP requests to other services."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize HTTP client adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._connected = False
        self._converter = HttpEnvelope()
        self.base_url = config.get("base_url", "")
        self.timeout = config.get("timeout", 30)
        self.headers = config.get("headers", {})
        self.session: requests.Session | None = None

    def connect(self) -> None:
        """Connect to HTTP service (create session).

        Raises:
            AdapterConnectionError: If connection setup fails.
        """
        if self._connected:
            logger.warning(f"HTTP client adapter '{self.name}' is already connected")
            return

        try:
            self.session = requests.Session()
            if self.headers:
                self.session.headers.update(self.headers)
            self._connected = True
            logger.info(f"HTTP client adapter '{self.name}' connected (base_url: {self.base_url})")
        except Exception as e:
            raise AdapterConnectionError(
                f"Failed to connect HTTP client adapter '{self.name}': {e}"
            ) from e

    def disconnect(self) -> None:
        """Disconnect from HTTP service (close session)."""
        if not self._connected:
            logger.warning(f"HTTP client adapter '{self.name}' is not connected")
            return

        try:
            if self.session:
                self.session.close()
                self.session = None
            self._connected = False
            logger.info(f"HTTP client adapter '{self.name}' disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting HTTP client adapter '{self.name}': {e}")

    def is_connected(self) -> bool:
        """Check if adapter is currently connected.

        Returns:
            True if connected, False otherwise.
        """
        return self._connected

    def from_envelope(self, envelope: Envelope) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Convert Envelope request to HTTP request.

        Args:
            envelope: Request envelope.

        Returns:
            Tuple of (method, url, headers, body_dict).
        """
        return self._converter.envelope_to_request(envelope, self.base_url)

    def to_envelope(
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
            original_envelope: Original request envelope.

        Returns:
            Response envelope.
        """
        return self._converter.response_to_envelope(status_code, data, headers, original_envelope)

    def request(self, envelope: Envelope) -> Envelope:
        """Make HTTP request using Envelope.

        Converts Envelope → HTTP Request → HTTP Response → Envelope.

        Args:
            envelope: Request envelope with path, method, body, headers, etc.

        Returns:
            Response envelope.

        Raises:
            RuntimeError: If adapter is not connected.
        """
        if not self._connected or not self.session:
            raise RuntimeError(f"HTTP client adapter '{self.name}' is not connected")

        # Convert Envelope → HTTP Request using converter
        method, url, request_headers, body = self.from_envelope(envelope)

        # Merge with default headers
        request_headers = {**self.headers, **request_headers}

        try:
            # Make HTTP request
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=envelope.query_params if envelope.query_params else None,
                json=body,
                headers=request_headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Convert HTTP Response → Envelope using converter
            try:
                response_data = response.json()
            except (ValueError, json.JSONDecodeError):
                response_data = {"raw": response.text}

            return self.to_envelope(
                status_code=response.status_code,
                data=response_data,
                headers=dict(response.headers),
                original_envelope=envelope,
            )
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {method} {url}: {e}")
            # Convert HTTP error to Envelope error
            status_code = e.response.status_code if hasattr(e, "response") and e.response else 500
            return Envelope.error(status_code, str(e))

