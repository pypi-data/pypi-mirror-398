"""Configuration loading and validation for HexSwitch."""

import logging
from pathlib import Path
import tomllib
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "hex-config.toml"


class ConfigError(Exception):
    """Raised when configuration validation fails."""

    pass


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        config_path: Path to configuration file. Defaults to hex-config.toml.

    Returns:
        Configuration dictionary.

    Raises:
        ConfigError: If configuration file cannot be loaded or is invalid.
    """
    if config_path is None:
        config_path = Path(DEFAULT_CONFIG_PATH)
    else:
        config_path = Path(config_path)

    # Check if file exists
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    # Load TOML
    try:
        with config_path.open("rb") as f:
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML syntax in {config_path}: {e}") from e
    except Exception as e:
        raise ConfigError(f"Error reading configuration file {config_path}: {e}") from e

    if not isinstance(config, dict):
        raise ConfigError(f"Configuration must be a dictionary, got {type(config).__name__}")

    # Check if config is empty (empty TOML file parses to empty dict)
    if not config:
        raise ConfigError(f"Configuration file is empty: {config_path}")

    return config


def validate_config(config: dict[str, Any]) -> None:
    """Validate configuration using Pydantic models.

    Args:
        config: Configuration dictionary to validate.

    Raises:
        ConfigError: If validation fails.
    """
    try:
        from hexswitch.shared.config.models import ConfigModel

        ConfigModel.from_dict(config)
    except ImportError as e:
        raise ConfigError(f"Failed to import config models: {e}") from e
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}") from e


def build_execution_plan(config: dict[str, Any]) -> dict[str, Any]:
    """Build execution plan from configuration.

    Args:
        config: Configuration dictionary (may contain Pydantic models after validation).

    Returns:
        Execution plan dictionary with service name and adapter lists.
    """
    plan: dict[str, Any] = {
        "service": config.get("service", {}).get("name", "unknown"),
        "inbound_adapters": [],
        "outbound_adapters": [],
    }

    # Extract inbound adapters
    inbound_config = config.get("inbound")
    if inbound_config is not None:
        # Handle both dict and Pydantic model
        if hasattr(inbound_config, "model_dump"):
            # Pydantic model - convert to dict
            inbound_dict = inbound_config.model_dump(exclude_none=True)
        elif isinstance(inbound_config, dict):
            inbound_dict = inbound_config
        else:
            inbound_dict = {}

        for adapter_name, adapter_config in inbound_dict.items():
            # Handle both dict and Pydantic model
            if hasattr(adapter_config, "model_dump"):
                adapter_dict = adapter_config.model_dump(exclude_none=True)
            elif isinstance(adapter_config, dict):
                adapter_dict = adapter_config
            else:
                continue

            if adapter_dict.get("enabled", False):
                plan["inbound_adapters"].append({
                    "name": adapter_name,
                    "config": adapter_dict,
                })

    # Extract outbound adapters
    outbound_config = config.get("outbound")
    if outbound_config is not None:
        # Handle both dict and Pydantic model
        if hasattr(outbound_config, "model_dump"):
            # Pydantic model - convert to dict
            outbound_dict = outbound_config.model_dump(exclude_none=True)
        elif isinstance(outbound_config, dict):
            outbound_dict = outbound_config
        else:
            outbound_dict = {}

        for adapter_name, adapter_config in outbound_dict.items():
            # Handle both dict and Pydantic model
            if hasattr(adapter_config, "model_dump"):
                adapter_dict = adapter_config.model_dump(exclude_none=True)
            elif isinstance(adapter_config, dict):
                adapter_dict = adapter_config
            else:
                continue

            if adapter_dict.get("enabled", False):
                plan["outbound_adapters"].append({
                    "name": adapter_name,
                    "config": adapter_dict,
                })

    return plan


def _validate_adapters(adapters: dict[str, Any], section_name: str) -> None:
    """Validate adapter configuration.

    Args:
        adapters: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    for adapter_name, adapter_config in adapters.items():
        if not isinstance(adapter_config, dict):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}' must be a dictionary"
            )

        # Check if 'enabled' flag exists and is boolean
        if "enabled" in adapter_config:
            if not isinstance(adapter_config["enabled"], bool):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    "'enabled' must be a boolean"
                )

        # Validate adapter-specific configuration
        if adapter_name == "http" and section_name == "inbound":
            _validate_http_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "http_client" and section_name == "outbound":
            _validate_http_client_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "mcp_client" and section_name == "outbound":
            _validate_mcp_client_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "grpc" and section_name == "inbound":
            _validate_grpc_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "grpc_client" and section_name == "outbound":
            _validate_grpc_client_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "websocket" and section_name == "inbound":
            _validate_websocket_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "websocket_client" and section_name == "outbound":
            _validate_websocket_client_adapter(adapter_name, adapter_config, section_name)
        elif adapter_name == "mcp" and section_name == "inbound":
            _validate_mcp_adapter(adapter_name, adapter_config, section_name)


def _validate_http_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate HTTP adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate base_path (optional, must be string if present)
    if "base_path" in adapter_config:
        if not isinstance(adapter_config["base_path"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'base_path' must be a string"
            )

    # Validate port (optional, must be integer if present)
    if "port" in adapter_config:
        if not isinstance(adapter_config["port"], int):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be an integer"
            )
        if not (1 <= adapter_config["port"] <= 65535):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be between 1 and 65535"
            )

    # Validate routes (optional, must be list if present)
    if "routes" in adapter_config:
        routes = adapter_config["routes"]
        if not isinstance(routes, list):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'routes' must be a list"
            )

        for i, route in enumerate(routes):
            if not isinstance(route, dict):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must be a dictionary"
                )

            # Validate required route fields
            if "path" not in route:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must contain 'path'"
                )
            if not isinstance(route["path"], str):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i}: 'path' must be a string"
                )

            if "method" not in route:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must contain 'method'"
                )
            if not isinstance(route["method"], str):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i}: 'method' must be a string"
                )
            if route["method"].upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i}: 'method' must be one of: GET, POST, PUT, DELETE, PATCH"
                )

            # Route must have either "handler" or "port"
            has_handler = "handler" in route
            has_port = "port" in route

            if not has_handler and not has_port:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must contain either 'handler' or 'port'"
                )

            if has_handler:
                if not isinstance(route["handler"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Route at index {i}: 'handler' must be a string"
                    )
                # Validate handler format (module:function)
                _validate_handler_reference(route["handler"], adapter_name, section_name, i)

            if has_port:
                if not isinstance(route["port"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Route at index {i}: 'port' must be a string"
                    )
                if not route["port"]:
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Route at index {i}: 'port' must not be empty"
                    )


def _validate_http_client_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate HTTP client adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate base_url (optional, must be string if present)
    if "base_url" in adapter_config:
        if not isinstance(adapter_config["base_url"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'base_url' must be a string"
            )

    # Validate timeout (optional, must be number if present)
    if "timeout" in adapter_config:
        if not isinstance(adapter_config["timeout"], (int, float)):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be a number"
            )
        if adapter_config["timeout"] <= 0:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be positive"
            )

    # Validate headers (optional, must be dict if present)
    if "headers" in adapter_config:
        if not isinstance(adapter_config["headers"], dict):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'headers' must be a dictionary"
            )


def _validate_mcp_client_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate MCP client adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate server_url (required)
    if "server_url" not in adapter_config:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' is required"
        )
    if not isinstance(adapter_config["server_url"], str):
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' must be a string"
        )
    if not adapter_config["server_url"]:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' must not be empty"
        )

    # Validate timeout (optional, must be number if present)
    if "timeout" in adapter_config:
        if not isinstance(adapter_config["timeout"], (int, float)):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be a number"
            )
        if adapter_config["timeout"] <= 0:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be positive"
            )

    # Validate headers (optional, must be dict if present)
    if "headers" in adapter_config:
        if not isinstance(adapter_config["headers"], dict):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'headers' must be a dictionary"
            )


def _validate_grpc_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate gRPC adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate port (optional, must be integer if present)
    if "port" in adapter_config:
        if not isinstance(adapter_config["port"], int):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be an integer"
            )
        if not (1 <= adapter_config["port"] <= 65535):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be between 1 and 65535"
            )

    # Validate proto_path (optional, must be string if present)
    if "proto_path" in adapter_config:
        if not isinstance(adapter_config["proto_path"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'proto_path' must be a string"
            )

    # Validate services (optional, must be list if present)
    if "services" in adapter_config:
        services = adapter_config["services"]
        if not isinstance(services, list):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'services' must be a list"
            )

        for i, service in enumerate(services):
            if not isinstance(service, dict):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Service at index {i} must be a dictionary"
                )

            if "service_name" not in service:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Service at index {i} must contain 'service_name'"
                )
            if not isinstance(service["service_name"], str):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Service at index {i}: 'service_name' must be a string"
                )

            if "methods" in service:
                methods = service["methods"]
                if not isinstance(methods, list):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Service at index {i}: 'methods' must be a list"
                    )

                for j, method in enumerate(methods):
                    if not isinstance(method, dict):
                        raise ConfigError(
                            f"Adapter '{adapter_name}' in section '{section_name}': "
                            f"Service at index {i}, method at index {j} must be a dictionary"
                        )

                    if "method_name" not in method:
                        raise ConfigError(
                            f"Adapter '{adapter_name}' in section '{section_name}': "
                            f"Service at index {i}, method at index {j} must contain 'method_name'"
                        )
                    if not isinstance(method["method_name"], str):
                        raise ConfigError(
                            f"Adapter '{adapter_name}' in section '{section_name}': "
                            f"Service at index {i}, method at index {j}: "
                            "'method_name' must be a string"
                        )

                    # Method must have either "handler" or "port"
                    has_handler = "handler" in method
                    has_port = "port" in method

                    if not has_handler and not has_port:
                        raise ConfigError(
                            f"Adapter '{adapter_name}' in section '{section_name}': "
                            f"Service at index {i}, method at index {j} must contain either 'handler' or 'port'"
                        )

                    if has_handler:
                        if not isinstance(method["handler"], str):
                            raise ConfigError(
                                f"Adapter '{adapter_name}' in section '{section_name}': "
                                f"Service at index {i}, method at index {j}: "
                                "'handler' must be a string"
                            )
                        _validate_handler_reference(
                            method["handler"], adapter_name, section_name, None
                        )

                    if has_port:
                        if not isinstance(method["port"], str):
                            raise ConfigError(
                                f"Adapter '{adapter_name}' in section '{section_name}': "
                                f"Service at index {i}, method at index {j}: "
                                "'port' must be a string"
                            )
                        if not method["port"]:
                            raise ConfigError(
                                f"Adapter '{adapter_name}' in section '{section_name}': "
                                f"Service at index {i}, method at index {j}: "
                                "'port' must not be empty"
                            )


def _validate_grpc_client_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate gRPC client adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate server_url (required)
    if "server_url" not in adapter_config:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' is required"
        )
    if not isinstance(adapter_config["server_url"], str):
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' must be a string"
        )
    if not adapter_config["server_url"]:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' must not be empty"
        )

    # Validate proto_path (optional, must be string if present)
    if "proto_path" in adapter_config:
        if not isinstance(adapter_config["proto_path"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'proto_path' must be a string"
            )

    # Validate service_name (optional, must be string if present)
    if "service_name" in adapter_config:
        if not isinstance(adapter_config["service_name"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'service_name' must be a string"
            )

    # Validate timeout (optional, must be number if present)
    if "timeout" in adapter_config:
        if not isinstance(adapter_config["timeout"], (int, float)):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be a number"
            )
        if adapter_config["timeout"] <= 0:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be positive"
            )


def _validate_websocket_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate WebSocket adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate port (optional, must be integer if present)
    if "port" in adapter_config:
        if not isinstance(adapter_config["port"], int):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be an integer"
            )
        if not (1 <= adapter_config["port"] <= 65535):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be between 1 and 65535"
            )

    # Validate path (optional, must be string if present)
    if "path" in adapter_config:
        if not isinstance(adapter_config["path"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'path' must be a string"
            )

    # Validate routes (optional, must be list if present)
    if "routes" in adapter_config:
        routes = adapter_config["routes"]
        if not isinstance(routes, list):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'routes' must be a list"
            )

        for i, route in enumerate(routes):
            if not isinstance(route, dict):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must be a dictionary"
                )

            if "path" not in route:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must contain 'path'"
                )
            if not isinstance(route["path"], str):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i}: 'path' must be a string"
                )

            # Route must have either "handler" or "port"
            has_handler = "handler" in route
            has_port = "port" in route

            if not has_handler and not has_port:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Route at index {i} must contain either 'handler' or 'port'"
                )

            if has_handler:
                if not isinstance(route["handler"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Route at index {i}: 'handler' must be a string"
                    )
                _validate_handler_reference(route["handler"], adapter_name, section_name, i)

            if has_port:
                if not isinstance(route["port"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Route at index {i}: 'port' must be a string"
                    )
                if not route["port"]:
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Route at index {i}: 'port' must not be empty"
                    )


def _validate_websocket_client_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate WebSocket client adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate url (required)
    if "url" not in adapter_config:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': " "'url' is required"
        )
    if not isinstance(adapter_config["url"], str):
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': " "'url' must be a string"
        )
    if not adapter_config["url"]:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': " "'url' must not be empty"
        )

    # Validate timeout (optional, must be number if present)
    if "timeout" in adapter_config:
        if not isinstance(adapter_config["timeout"], (int, float)):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be a number"
            )
        if adapter_config["timeout"] <= 0:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be positive"
            )

    # Validate reconnect (optional, must be boolean if present)
    if "reconnect" in adapter_config:
        if not isinstance(adapter_config["reconnect"], bool):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'reconnect' must be a boolean"
            )

    # Validate reconnect_interval (optional, must be number if present)
    if "reconnect_interval" in adapter_config:
        if not isinstance(adapter_config["reconnect_interval"], (int, float)):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'reconnect_interval' must be a number"
            )
        if adapter_config["reconnect_interval"] <= 0:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'reconnect_interval' must be positive"
            )


def _validate_mcp_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate MCP inbound adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate server_url (required)
    if "server_url" not in adapter_config:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' is required"
        )
    if not isinstance(adapter_config["server_url"], str):
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' must be a string"
        )
    if not adapter_config["server_url"]:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'server_url' must not be empty"
        )

    # Validate port (optional, must be integer if present)
    if "port" in adapter_config:
        if not isinstance(adapter_config["port"], int):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be an integer"
            )
        if not (1 <= adapter_config["port"] <= 65535):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'port' must be between 1 and 65535"
            )

    # Validate methods (optional, must be list if present)
    if "methods" in adapter_config:
        methods = adapter_config["methods"]
        if not isinstance(methods, list):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'methods' must be a list"
            )

        for i, method in enumerate(methods):
            if not isinstance(method, dict):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Method at index {i} must be a dictionary"
                )

            if "method_name" not in method:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Method at index {i} must contain 'method_name'"
                )
            if not isinstance(method["method_name"], str):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Method at index {i}: 'method_name' must be a string"
                )

            # Method must have either "handler" or "port"
            has_handler = "handler" in method
            has_port = "port" in method

            if not has_handler and not has_port:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Method at index {i} must contain either 'handler' or 'port'"
                )

            if has_handler:
                if not isinstance(method["handler"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Method at index {i}: 'handler' must be a string"
                    )
                _validate_handler_reference(
                    method["handler"], adapter_name, section_name, None
                )

            if has_port:
                if not isinstance(method["port"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Method at index {i}: 'port' must be a string"
                    )
                if not method["port"]:
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Method at index {i}: 'port' must not be empty"
                    )


def _validate_nats_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate NATS inbound adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate servers (required)
    if "servers" not in adapter_config:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'servers' is required"
        )
    # Validate servers (must be string or list if present)
    if "servers" in adapter_config:
        servers = adapter_config["servers"]
        if isinstance(servers, str):
            pass  # Valid
        elif isinstance(servers, list):
            for i, server in enumerate(servers):
                if not isinstance(server, str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Server at index {i} must be a string"
                    )
        else:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'servers' must be a string or list of strings"
            )

    # Validate subjects (optional, must be list if present)
    if "subjects" in adapter_config:
        subjects = adapter_config["subjects"]
        if not isinstance(subjects, list):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'subjects' must be a list"
            )

        for i, subject_config in enumerate(subjects):
            if not isinstance(subject_config, dict):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Subject at index {i} must be a dictionary"
                )

            if "subject" not in subject_config:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Subject at index {i} must contain 'subject'"
                )
            if not isinstance(subject_config["subject"], str):
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Subject at index {i}: 'subject' must be a string"
                )

            # Subject must have either "handler" or "port"
            has_handler = "handler" in subject_config
            has_port = "port" in subject_config

            if not has_handler and not has_port:
                raise ConfigError(
                    f"Adapter '{adapter_name}' in section '{section_name}': "
                    f"Subject at index {i} must contain either 'handler' or 'port'"
                )

            if has_handler:
                if not isinstance(subject_config["handler"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Subject at index {i}: 'handler' must be a string"
                    )
                _validate_handler_reference(
                    subject_config["handler"], adapter_name, section_name, i
                )

            if has_port:
                if not isinstance(subject_config["port"], str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Subject at index {i}: 'port' must be a string"
                    )
                if not subject_config["port"]:
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Subject at index {i}: 'port' must not be empty"
                    )

    # Validate queue_group (optional, must be string if present)
    if "queue_group" in adapter_config:
        if not isinstance(adapter_config["queue_group"], str):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'queue_group' must be a string"
            )


def _validate_nats_client_adapter(
    adapter_name: str, adapter_config: dict[str, Any], section_name: str
) -> None:
    """Validate NATS client adapter configuration.

    Args:
        adapter_name: Name of the adapter.
        adapter_config: Adapter configuration dictionary.
        section_name: Name of the section (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    # Validate servers (required)
    if "servers" not in adapter_config:
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}': "
            "'servers' is required"
        )
    # Validate servers (must be string or list if present)
    if "servers" in adapter_config:
        servers = adapter_config["servers"]
        if isinstance(servers, str):
            pass  # Valid
        elif isinstance(servers, list):
            for i, server in enumerate(servers):
                if not isinstance(server, str):
                    raise ConfigError(
                        f"Adapter '{adapter_name}' in section '{section_name}': "
                        f"Server at index {i} must be a string"
                    )
        else:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'servers' must be a string or list of strings"
            )

    # Validate timeout (optional, must be number if present)
    if "timeout" in adapter_config:
        if not isinstance(adapter_config["timeout"], (int, float)):
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be a number"
            )
        if adapter_config["timeout"] <= 0:
            raise ConfigError(
                f"Adapter '{adapter_name}' in section '{section_name}': "
                "'timeout' must be positive"
            )


def _validate_handler_reference(
    handler_path: str, adapter_name: str, section_name: str, route_index: int | None = None
) -> None:
    """Validate handler reference format.

    Args:
        handler_path: Handler reference string.
        adapter_name: Name of the adapter (for error messages).
        section_name: Name of the section (for error messages).
        route_index: Optional route index (for error messages).

    Raises:
        ConfigError: If validation fails.
    """
    if ":" not in handler_path:
        route_info = f" at route index {route_index}" if route_index is not None else ""
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}'{route_info}: "
            f"Invalid handler format '{handler_path}'. "
            "Expected format: 'module.path:function_name'"
        )

    module_path, function_name = handler_path.rsplit(":", 1)

    if not module_path or not function_name:
        route_info = f" at route index {route_index}" if route_index is not None else ""
        raise ConfigError(
            f"Adapter '{adapter_name}' in section '{section_name}'{route_info}: "
            f"Invalid handler format '{handler_path}'. "
            "Module path and function name must not be empty."
        )


def get_example_config() -> str:
    """Generate example configuration file content.

    Returns:
        Example configuration as TOML string.
    """
    return """[service]
name = "example-service"
runtime = "python"

[inbound.http]
enabled = true
port = 8000
base_path = "/api"

[[inbound.http.routes]]
path = "/hello"
method = "GET"
handler = "adapters.http_handlers:hello"

[outbound.http_client]
enabled = false
base_url = "https://api.example.com"
timeout = 30

[outbound.mcp_client]
enabled = false
server_url = "https://mcp.example.com"
timeout = 30

[logging]
level = "INFO"
"""
