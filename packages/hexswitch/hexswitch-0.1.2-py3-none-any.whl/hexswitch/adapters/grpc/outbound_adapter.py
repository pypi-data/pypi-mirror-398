"""gRPC client outbound adapter implementation."""

import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import grpc

from hexswitch.adapters.base import OutboundAdapter
from hexswitch.adapters.exceptions import AdapterConnectionError
from hexswitch.adapters.grpc._Grpc_Envelope import GrpcEnvelope
from hexswitch.shared.envelope import Envelope

logger = logging.getLogger(__name__)


def compile_proto_files(proto_path: str, output_dir: str) -> None:
    """Compile .proto files to Python code.

    Args:
        proto_path: Path to directory containing .proto files.
        output_dir: Directory to output compiled Python files.

    Raises:
        RuntimeError: If compilation fails.
    """
    proto_path_obj = Path(proto_path)
    if not proto_path_obj.exists():
        raise RuntimeError(f"Proto path does not exist: {proto_path}")

    proto_files = list(proto_path_obj.glob("*.proto"))
    if not proto_files:
        raise RuntimeError(f"No .proto files found in {proto_path}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Add output directory to Python path
    if str(output_path) not in sys.path:
        sys.path.insert(0, str(output_path))

    for proto_file in proto_files:
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "grpc_tools.protoc",
                    f"--proto_path={proto_path_obj.parent}",
                    f"--python_out={output_dir}",
                    f"--grpc_python_out={output_dir}",
                    str(proto_file),
                ],
                check=True,
                capture_output=True,
            )
            logger.debug(f"Compiled proto file: {proto_file}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to compile proto file {proto_file}: {e.stderr.decode() if e.stderr else 'Unknown error'}"
            ) from e


class GrpcAdapterClient(OutboundAdapter):
    """gRPC client outbound adapter for making gRPC calls to other services."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize gRPC client adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._connected = False
        self._converter = GrpcEnvelope()
        self.server_url = config.get("server_url", "")
        self.proto_path = config.get("proto_path", "")
        self.service_name = config.get("service_name", "")
        self.timeout = config.get("timeout", 30)
        self.channel: grpc.Channel | None = None
        self.stub: Any | None = None
        self._compiled_proto_dir: str | None = None

    def connect(self) -> None:
        """Connect to gRPC service (create channel and stub).

        Raises:
            AdapterConnectionError: If connection setup fails.
        """
        if self._connected:
            logger.warning(f"gRPC client adapter '{self.name}' is already connected")
            return

        try:
            if not self.server_url:
                raise ValueError("server_url is required")

            # Compile proto files if proto_path is provided
            if self.proto_path:
                self._compiled_proto_dir = tempfile.mkdtemp(prefix="hexswitch_grpc_client_")
                compile_proto_files(self.proto_path, self._compiled_proto_dir)
                logger.info(f"Compiled proto files to {self._compiled_proto_dir}")

                # Try to dynamically import the service stub
                # This is simplified - in production, you'd load the actual generated stub
                logger.info(f"Service stub for {self.service_name} would be loaded here")

            # Create channel
            self.channel = grpc.insecure_channel(self.server_url)

            # Wait for channel to be ready (with timeout)
            try:
                grpc.channel_ready_future(self.channel).result(timeout=self.timeout)
            except grpc.FutureTimeoutError as e:
                raise AdapterConnectionError(
                    f"Failed to connect to gRPC server '{self.server_url}': timeout"
                ) from e

            # Create stub (simplified - would use actual generated stub in production)
            # For now, we store the channel and service name
            self.stub = {"channel": self.channel, "service_name": self.service_name}

            self._connected = True
            logger.info(
                f"gRPC client adapter '{self.name}' connected to {self.server_url} "
                f"(service: {self.service_name})"
            )
        except Exception as e:
            raise AdapterConnectionError(
                f"Failed to connect gRPC client adapter '{self.name}': {e}"
            ) from e

    def disconnect(self) -> None:
        """Disconnect from gRPC service (close channel)."""
        if not self._connected:
            logger.warning(f"gRPC client adapter '{self.name}' is not connected")
            return

        try:
            if self.channel:
                self.channel.close()
                self.channel = None
            self.stub = None

            # Cleanup compiled proto files
            if self._compiled_proto_dir and os.path.exists(self._compiled_proto_dir):
                import shutil

                shutil.rmtree(self._compiled_proto_dir, ignore_errors=True)
                logger.debug(f"Cleaned up compiled proto directory: {self._compiled_proto_dir}")

            self._connected = False
            logger.info(f"gRPC client adapter '{self.name}' disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting gRPC client adapter '{self.name}': {e}")

    def from_envelope(self, envelope: Envelope) -> dict[str, Any]:
        """Convert Envelope request to gRPC request.

        Args:
            envelope: Request envelope.

        Returns:
            Request data dictionary (to be converted to protobuf message).
        """
        return self._converter.envelope_to_request(envelope)

    def to_envelope(
        self,
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
        return self._converter.response_to_envelope(response, original_envelope)

    def request(self, envelope: Envelope) -> Envelope:
        """Make gRPC request using Envelope.

        Converts Envelope → gRPC Request → gRPC Response → Envelope.

        Args:
            envelope: Request envelope with path, body, metadata, etc.

        Returns:
            Response envelope.

        Raises:
            RuntimeError: If adapter is not connected.
        """
        if not self._connected or not self.channel or not self.stub:
            raise RuntimeError(f"gRPC client adapter '{self.name}' is not connected")

        # Extract method name from path (e.g., "/ServiceName/MethodName" -> "MethodName")
        path_parts = envelope.path.strip("/").split("/")
        method_name = path_parts[-1] if path_parts else "unknown"

        # Extract metadata
        envelope.metadata.get("grpc_metadata", {})

        # Convert Envelope body to gRPC request using converter
        self.from_envelope(envelope)

        # TODO: Convert request_dict to protobuf message using compiled stubs
        # For now, we'll use a simplified approach

        call_timeout = self.timeout

        try:
            # This is a simplified implementation
            # In production, you would use the actual generated stub method
            # For example: response = self.stub.MethodName(request, timeout=call_timeout, metadata=grpc_metadata)
            logger.debug(f"Calling {self.service_name}.{method_name} with timeout {call_timeout}")

            # Placeholder - would use actual stub method here
            # For now, return error indicating stub is needed
            return Envelope.error(
                501,
                "gRPC method calls require compiled proto stubs. "
                "This is a simplified implementation that needs the actual service stub."
            )
        except grpc.RpcError as e:
            logger.error(f"gRPC call failed: {method_name}: {e}")
            # Convert gRPC error to Envelope error using converter
            status_code = e.code() if hasattr(e, "code") else grpc.StatusCode.INTERNAL
            error_message = e.details() if hasattr(e, "details") else str(e)
            return self._converter.error_to_envelope(status_code, error_message, envelope)

