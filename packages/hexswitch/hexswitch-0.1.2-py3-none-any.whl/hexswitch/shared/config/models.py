"""Pydantic models for configuration validation."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class GuiConfig(BaseModel):
    """GUI configuration."""

    enabled: bool = Field(False, description="Enable GUI server")
    port: int = Field(8080, ge=1, le=65535, description="GUI server port")


class ServiceConfig(BaseModel):
    """Service configuration."""

    name: str = Field(..., description="Service name")
    version: str | None = Field(None, description="Service version")
    runtime: str = Field("python", description="Runtime type")
    gui: GuiConfig | None = Field(None, description="GUI configuration")


class HttpRouteConfig(BaseModel):
    """HTTP route configuration."""

    path: str = Field(..., description="Route path")
    method: str = Field(..., description="HTTP method")
    handler: str | None = Field(None, description="Handler function path")
    port: str | None = Field(None, description="Port name")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate HTTP method."""
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if v.upper() not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")
        return v.upper()

    @model_validator(mode="after")
    def validate_handler_or_port(self) -> "HttpRouteConfig":
        """Ensure either handler or port is provided."""
        if self.handler is None and self.port is None:
            raise ValueError("Either 'handler' or 'port' must be provided")
        if self.handler and ":" not in self.handler:
            raise ValueError(
                "Handler must be in format 'module.path:function_name'"
            )
        return self


class HttpInboundConfig(BaseModel):
    """HTTP inbound adapter configuration."""

    enabled: bool = Field(False, description="Enable HTTP adapter")
    port: int = Field(8000, ge=1, le=65535, description="HTTP port")
    base_path: str = Field("", description="Base path prefix")
    routes: list[HttpRouteConfig] = Field(
        default_factory=list, description="HTTP routes"
    )
    enable_default_routes: bool = Field(
        True, description="Enable default health and metrics routes"
    )


class HttpClientConfig(BaseModel):
    """HTTP client adapter configuration."""

    enabled: bool = Field(False, description="Enable HTTP client adapter")
    base_url: str | None = Field(None, description="Base URL for HTTP client")
    timeout: float | int = Field(30.0, gt=0, description="Request timeout in seconds")
    headers: dict[str, str] | None = Field(None, description="Default headers")
    ports: list[str] | None = Field(None, description="List of port names to register this adapter on")


class McpClientConfig(BaseModel):
    """MCP client adapter configuration."""

    enabled: bool = Field(False, description="Enable MCP client adapter")
    server_url: str = Field(..., description="MCP server URL")
    timeout: float | int = Field(30.0, gt=0, description="Request timeout in seconds")
    headers: dict[str, str] | None = Field(None, description="Default headers")


class GrpcServiceMethodConfig(BaseModel):
    """gRPC service method configuration."""

    method_name: str = Field(..., description="gRPC method name")
    handler: str | None = Field(None, description="Handler function path")
    port: str | None = Field(None, description="Port name")

    @model_validator(mode="after")
    def validate_handler_or_port(self) -> "GrpcServiceMethodConfig":
        """Ensure either handler or port is provided."""
        if self.handler is None and self.port is None:
            raise ValueError("Either 'handler' or 'port' must be provided")
        if self.handler and ":" not in self.handler:
            raise ValueError(
                "Handler must be in format 'module.path:function_name'"
            )
        return self


class GrpcServiceConfig(BaseModel):
    """gRPC service configuration."""

    service_name: str = Field(..., description="gRPC service name")
    methods: list[GrpcServiceMethodConfig] = Field(
        default_factory=list, description="gRPC methods"
    )


class GrpcInboundConfig(BaseModel):
    """gRPC inbound adapter configuration."""

    enabled: bool = Field(False, description="Enable gRPC adapter")
    port: int = Field(50051, ge=1, le=65535, description="gRPC port")
    proto_path: str | None = Field(None, description="Path to proto file")
    services: list[GrpcServiceConfig] = Field(
        default_factory=list, description="gRPC services"
    )


class GrpcClientConfig(BaseModel):
    """gRPC client adapter configuration."""

    enabled: bool = Field(False, description="Enable gRPC client adapter")
    server_url: str = Field(..., description="gRPC server URL")
    proto_path: str | None = Field(None, description="Path to proto file")
    service_name: str | None = Field(None, description="gRPC service name")
    timeout: float | int = Field(30.0, gt=0, description="Request timeout in seconds")


class WebSocketRouteConfig(BaseModel):
    """WebSocket route configuration."""

    path: str = Field(..., description="Route path")
    handler: str | None = Field(None, description="Handler function path")
    port: str | None = Field(None, description="Port name")

    @model_validator(mode="after")
    def validate_handler_or_port(self) -> "WebSocketRouteConfig":
        """Ensure either handler or port is provided."""
        if self.handler is None and self.port is None:
            raise ValueError("Either 'handler' or 'port' must be provided")
        if self.handler and ":" not in self.handler:
            raise ValueError(
                "Handler must be in format 'module.path:function_name'"
            )
        return self


class WebSocketInboundConfig(BaseModel):
    """WebSocket inbound adapter configuration."""

    enabled: bool = Field(False, description="Enable WebSocket adapter")
    port: int = Field(8001, ge=1, le=65535, description="WebSocket port")
    path: str | None = Field(None, description="WebSocket path")
    routes: list[WebSocketRouteConfig] = Field(
        default_factory=list, description="WebSocket routes"
    )


class WebSocketClientConfig(BaseModel):
    """WebSocket client adapter configuration."""

    enabled: bool = Field(False, description="Enable WebSocket client adapter")
    url: str = Field(..., description="WebSocket server URL")
    timeout: float | int = Field(30.0, gt=0, description="Connection timeout in seconds")
    reconnect: bool = Field(False, description="Enable automatic reconnection")
    reconnect_interval: float | int = Field(
        5.0, gt=0, description="Reconnection interval in seconds"
    )


class NatsSubjectConfig(BaseModel):
    """NATS subject configuration."""

    subject: str = Field(..., description="NATS subject to subscribe to")
    handler: str | None = Field(None, description="Handler function path")
    port: str | None = Field(None, description="Port name")

    @model_validator(mode="after")
    def validate_handler_or_port(self) -> "NatsSubjectConfig":
        """Ensure either handler or port is provided."""
        if self.handler is None and self.port is None:
            raise ValueError("Either 'handler' or 'port' must be provided")
        if self.handler and ":" not in self.handler:
            raise ValueError(
                "Handler must be in format 'module.path:function_name'"
            )
        return self


class NatsInboundConfig(BaseModel):
    """NATS inbound adapter configuration."""

    enabled: bool = Field(False, description="Enable NATS adapter")
    servers: list[str] | str = Field(
        ["nats://localhost:4222"], description="NATS server URLs"
    )
    subjects: list[NatsSubjectConfig] = Field(
        default_factory=list, description="NATS subjects to subscribe to"
    )
    queue_group: str | None = Field(None, description="Queue group for load balancing")


class NatsClientConfig(BaseModel):
    """NATS client adapter configuration."""

    enabled: bool = Field(False, description="Enable NATS client adapter")
    servers: list[str] | str = Field(
        ["nats://localhost:4222"], description="NATS server URLs"
    )
    timeout: float | int = Field(30.0, gt=0, description="Request timeout in seconds")


class InboundConfig(BaseModel):
    """Inbound adapters configuration."""

    http: HttpInboundConfig | None = None
    grpc: GrpcInboundConfig | None = None
    websocket: WebSocketInboundConfig | None = None
    nats: NatsInboundConfig | None = None


class OutboundConfig(BaseModel):
    """Outbound adapters configuration."""

    http_client: HttpClientConfig | None = None
    grpc_client: GrpcClientConfig | None = None
    websocket_client: WebSocketClientConfig | None = None
    mcp_client: McpClientConfig | None = None
    nats_client: NatsClientConfig | None = None


class RoutingStrategy(str, Enum):
    """Routing strategy options."""

    FIRST = "first"
    BROADCAST = "broadcast"
    ROUND_ROBIN = "round_robin"


class RetryPolicy(BaseModel):
    """Retry policy configuration."""

    enabled: bool = Field(False, description="Enable retry")
    max_attempts: int = Field(3, ge=1, description="Maximum retry attempts")
    initial_delay: float = Field(1.0, ge=0, description="Initial delay in seconds")
    max_delay: float = Field(60.0, ge=0, description="Maximum delay in seconds")
    backoff_multiplier: float = Field(2.0, ge=1.0, description="Backoff multiplier")
    retryable_errors: list[str] = Field(
        default_factory=lambda: ["500", "502", "503", "504", "timeout"],
        description="List of retryable error codes/types",
    )


class TimeoutPolicy(BaseModel):
    """Timeout policy configuration."""

    enabled: bool = Field(False, description="Enable timeout")
    timeout_seconds: float = Field(30.0, gt=0, description="Timeout in seconds")


class BackpressurePolicy(BaseModel):
    """Backpressure policy configuration."""

    enabled: bool = Field(False, description="Enable backpressure")
    max_concurrent: int = Field(10, ge=1, description="Maximum concurrent requests")
    queue_size: int = Field(100, ge=0, description="Maximum queue size")
    rejection_strategy: str = Field(
        "fail_fast", description="Rejection strategy: fail_fast, queue, or drop"
    )


class RoutingPolicies(BaseModel):
    """Routing policies configuration."""

    retry: RetryPolicy | None = Field(None, description="Retry policy")
    timeout: TimeoutPolicy | None = Field(None, description="Timeout policy")
    backpressure: BackpressurePolicy | None = Field(
        None, description="Backpressure policy"
    )


class PortConfig(BaseModel):
    """Port-specific configuration."""

    routing_strategy: RoutingStrategy | None = Field(
        None, description="Routing strategy for this port"
    )
    policies: RoutingPolicies | None = Field(
        None, description="Routing policies for this port"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field("INFO", description="Log level")


class ConfigModel(BaseModel):
    """Root configuration model."""

    service: ServiceConfig
    inbound: InboundConfig | None = None
    outbound: OutboundConfig | None = None
    logging: LoggingConfig | None = None
    ports: dict[str, PortConfig] | None = Field(
        None, description="Port-specific configuration"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigModel":
        """Create config model from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            ConfigModel instance.
        """
        # Parse nested configs
        if "inbound" in data and isinstance(data["inbound"], dict):
            inbound_data = data["inbound"]
            parsed_inbound: dict[str, Any] = {}
            if "http" in inbound_data:
                parsed_inbound["http"] = HttpInboundConfig(**inbound_data["http"])
            if "grpc" in inbound_data:
                parsed_inbound["grpc"] = GrpcInboundConfig(**inbound_data["grpc"])
            if "websocket" in inbound_data:
                parsed_inbound["websocket"] = WebSocketInboundConfig(
                    **inbound_data["websocket"]
                )
            if "nats" in inbound_data:
                parsed_inbound["nats"] = NatsInboundConfig(**inbound_data["nats"])
            data["inbound"] = InboundConfig(**parsed_inbound) if parsed_inbound else None

        if "outbound" in data and isinstance(data["outbound"], dict):
            outbound_data = data["outbound"]
            parsed_outbound: dict[str, Any] = {}
            if "http_client" in outbound_data:
                parsed_outbound["http_client"] = HttpClientConfig(
                    **outbound_data["http_client"]
                )
            if "grpc_client" in outbound_data:
                parsed_outbound["grpc_client"] = GrpcClientConfig(
                    **outbound_data["grpc_client"]
                )
            if "websocket_client" in outbound_data:
                parsed_outbound["websocket_client"] = WebSocketClientConfig(
                    **outbound_data["websocket_client"]
                )
            if "mcp_client" in outbound_data:
                parsed_outbound["mcp_client"] = McpClientConfig(
                    **outbound_data["mcp_client"]
                )
            if "nats_client" in outbound_data:
                parsed_outbound["nats_client"] = NatsClientConfig(
                    **outbound_data["nats_client"]
                )
            data["outbound"] = (
                OutboundConfig(**parsed_outbound) if parsed_outbound else None
            )

        if "logging" in data:
            data["logging"] = LoggingConfig(**data["logging"])

        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Configuration dictionary.
        """
        return self.model_dump(exclude_none=True)


# Rebuild models to resolve forward references after all classes are defined
InboundConfig.model_rebuild()
OutboundConfig.model_rebuild()
PortConfig.model_rebuild()
RoutingPolicies.model_rebuild()
ConfigModel.model_rebuild()

