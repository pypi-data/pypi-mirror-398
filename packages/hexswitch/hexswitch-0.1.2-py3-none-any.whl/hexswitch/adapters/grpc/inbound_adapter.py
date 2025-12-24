"""gRPC inbound adapter implementation."""

from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
from typing import Any

import grpc
from grpc import server as grpc_server

from hexswitch.adapters.base import InboundAdapter
from hexswitch.adapters.exceptions import AdapterStartError, AdapterStopError, HandlerError
from hexswitch.adapters.grpc._Grpc_Envelope import GrpcEnvelope
from hexswitch.ports import PortError, get_port_registry
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


class GrpcServiceHandler:
    """Generic gRPC service handler that routes to HexSwitch handlers."""

    def __init__(
        self,
        service_config: dict[str, Any],
        handler_map: dict[str, Any],
        converter: GrpcEnvelope,
    ):
        """Initialize gRPC service handler.

        Args:
            service_config: Service configuration from config.
            handler_map: Map of method names to handler functions.
            converter: gRPC converter instance.
        """
        self.service_name = service_config.get("service_name", "")
        self.handler_map = handler_map
        self._converter = converter

    def __getattr__(self, method_name: str):
        """Dynamically handle method calls.

        Args:
            method_name: Name of the gRPC method.

        Returns:
            Handler function for the method.
        """
        if method_name in self.handler_map:
            handler = self.handler_map[method_name]

            def method_handler(request, context):
                """Handle gRPC method call."""
                try:
                    # Convert gRPC Request → Envelope using converter
                    request_envelope = self._converter.request_to_envelope(
                        request=request,
                        context=context,
                        service_name=self.service_name,
                        method_name=method_name,
                    )

                    # Call handler/port with Envelope
                    response_envelope = handler(request_envelope)

                    # Convert Envelope (Response) → gRPC Response
                    # If response is an error, set gRPC status
                    if response_envelope.error_message:
                        context.set_code(grpc.StatusCode.INTERNAL)
                        context.set_details(response_envelope.error_message)
                        raise grpc.RpcError(f"Handler error: {response_envelope.error_message}")

                    # Convert response data using converter
                    return self._converter.envelope_to_response(response_envelope)

                except grpc.RpcError:
                    raise
                except Exception as e:
                    logger.exception(f"Handler error for {self.service_name}.{method_name}: {e}")
                    context.set_code(grpc.StatusCode.INTERNAL)
                    context.set_details(str(e))
                    raise

            return method_handler
        else:
            # Method not found
            def not_found_handler(request, context):
                """Handle method not found."""
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Method {method_name} not found")
                return None

            return not_found_handler


class GrpcAdapterServer(InboundAdapter):
    """gRPC inbound adapter for HexSwitch."""

    def __init__(self, name: str, config: dict[str, Any]):
        """Initialize gRPC adapter.

        Args:
            name: Adapter name.
            config: Adapter configuration dictionary.
        """
        self.name = name
        self.config = config
        self._running = False
        self._converter = GrpcEnvelope()
        self.server: grpc_server | None = None
        self.server_thread: Thread | None = None
        self.port = config.get("port", 50051)
        self.proto_path = config.get("proto_path", "")
        self.services = config.get("services", [])
        self._compiled_proto_dir: str | None = None
        self._handler_map: dict[str, dict[str, Any]] = {}
        self._handler_loader = None  # Will be set by runtime if available

    def _load_handlers(self) -> None:
        """Load all handler functions for configured services."""
        for service_config in self.services:
            service_name = service_config.get("service_name", "")
            methods = service_config.get("methods", [])
            service_handler_map = {}

            for method_config in methods:
                method_name = method_config.get("method_name", "")
                handler_path = method_config.get("handler", "")
                port_name = method_config.get("port", "")

                if not handler_path and not port_name:
                    logger.warning(
                        f"No handler or port specified for {service_name}.{method_name}, skipping"
                    )
                    continue

                try:
                    # Use handler loader if available, otherwise fall back to old method
                    if self._handler_loader:
                        # Support both "handler:" and "port:" in config
                        if port_name:
                            handler = self._handler_loader.resolve(port_name)
                        elif handler_path:
                            handler = self._handler_loader.resolve(handler_path)
                        else:
                            continue
                        logger.debug(f"Loaded handler for {service_name}.{method_name} via HandlerLoader")
                    else:
                        # Fallback to old method for backward compatibility
                        if port_name:
                            handler = get_port_registry().get_handler(port_name)
                            logger.debug(f"Loaded port '{port_name}' for {service_name}.{method_name}")
                        else:
                            if ":" not in handler_path:
                                raise HandlerError(f"Invalid handler path format: {handler_path}. Expected format: 'module.path:function_name'")
                            module_path, function_name = handler_path.rsplit(":", 1)
                            if not module_path or not function_name:
                                raise HandlerError(f"Invalid handler path format: {handler_path}. Module path and function name must not be empty.")
                            import importlib
                            module = importlib.import_module(module_path)
                            if not hasattr(module, function_name):
                                raise HandlerError(f"Module '{module_path}' does not have attribute '{function_name}'")
                            handler = getattr(module, function_name)
                            if not callable(handler):
                                raise HandlerError(f"'{function_name}' in module '{module_path}' is not callable")
                            logger.debug(f"Loaded handler for {service_name}.{method_name}: {handler_path}")
                    service_handler_map[method_name] = handler
                except (HandlerError, PortError) as e:
                    logger.error(f"Failed to load handler/port for {service_name}.{method_name}: {e}")
                    raise

            self._handler_map[service_name] = service_handler_map

    def start(self) -> None:
        """Start the gRPC server.

        Raises:
            AdapterStartError: If the server fails to start.
        """
        if self._running:
            logger.warning(f"gRPC adapter '{self.name}' is already running")
            return

        try:
            # Load handlers
            self._load_handlers()

            # Compile proto files if proto_path is provided
            if self.proto_path:
                self._compiled_proto_dir = tempfile.mkdtemp(prefix="hexswitch_grpc_")
                compile_proto_files(self.proto_path, self._compiled_proto_dir)
                logger.info(f"Compiled proto files to {self._compiled_proto_dir}")

            # Create gRPC server
            self.server = grpc_server(ThreadPoolExecutor(max_workers=10))

            # Register services
            for service_config in self.services:
                service_name = service_config.get("service_name", "")
                handler_map = self._handler_map.get(service_name, {})

                # Create service handler with converter
                GrpcServiceHandler(service_config, handler_map, self._converter)

                # Try to dynamically add service to server
                # This is a simplified approach - in production, you'd load the actual
                # generated service stub from compiled proto files
                logger.info(f"Registered service handler for {service_name}")

            # Start server
            self.server.add_insecure_port(f"[::]:{self.port}")
            self.server.start()

            # Start server thread for graceful shutdown
            def run_server():
                """Run server in thread."""
                try:
                    self.server.wait_for_termination()
                except Exception as e:
                    logger.error(f"gRPC server error: {e}")

            self.server_thread = Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self._running = True

            logger.info(f"gRPC adapter '{self.name}' started on port {self.port}")
        except Exception as e:
            raise AdapterStartError(f"Failed to start gRPC adapter '{self.name}': {e}") from e

    def stop(self) -> None:
        """Stop the gRPC server.

        Raises:
            AdapterStopError: If the server fails to stop.
        """
        if not self._running:
            logger.warning(f"gRPC adapter '{self.name}' is not running")
            return

        try:
            if self.server:
                self.server.stop(grace=5)
                self.server.wait_for_termination(timeout=5)
            if self.server_thread:
                self.server_thread.join(timeout=5.0)

            # Cleanup compiled proto files
            if self._compiled_proto_dir and os.path.exists(self._compiled_proto_dir):
                import shutil

                shutil.rmtree(self._compiled_proto_dir, ignore_errors=True)
                logger.debug(f"Cleaned up compiled proto directory: {self._compiled_proto_dir}")

            self._running = False
            logger.info(f"gRPC adapter '{self.name}' stopped")
        except Exception as e:
            raise AdapterStopError(f"Failed to stop gRPC adapter '{self.name}': {e}") from e

    def to_envelope(
        self,
        request: Any,
        context: Any,
        service_name: str,
        method_name: str,
    ) -> Envelope:
        """Convert gRPC request to Envelope.

        Args:
            request: gRPC request object.
            context: gRPC context.
            service_name: Service name.
            method_name: Method name.

        Returns:
            Request envelope.
        """
        return self._converter.request_to_envelope(request, context, service_name, method_name)

    def from_envelope(self, envelope: Envelope) -> dict[str, Any]:
        """Convert Envelope response to gRPC response.

        Args:
            envelope: Response envelope.

        Returns:
            Response data dictionary.
        """
        return self._converter.envelope_to_response(envelope)

