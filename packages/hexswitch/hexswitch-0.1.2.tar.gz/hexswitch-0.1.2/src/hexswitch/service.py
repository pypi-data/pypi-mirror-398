"""HexSwitchService - Simple entry point for framework usage.

This module provides HexSwitchService, a base class that automatically handles
runtime initialization, configuration loading, and lifecycle management.
"""

import os
from pathlib import Path
import signal
from typing import Any

from hexswitch.runtime import Runtime
from hexswitch.shared.config import (
    DEFAULT_CONFIG_PATH,
    load_config,
    validate_config,
)
from hexswitch.shared.config.config import ConfigError  # noqa: F401
from hexswitch.shared.logging import get_logger

logger = get_logger(__name__)


def _load_env_overrides(prefix: str = "HEX_") -> dict[str, Any]:
    """Load configuration overrides from environment variables.

    Environment variables starting with the prefix are converted to nested
    configuration paths. Field names with underscores are preserved.
    For example:
    - HEX_SERVICE_NAME -> service.name
    - HEX_INBOUND_HTTP_PORT -> inbound.http.port
    - HEX_INBOUND_HTTP_BASE_PATH -> inbound.http.base_path
    - HEX_LOGGING_LEVEL -> logging.level

    Args:
        prefix: Prefix for environment variables (default: "HEX_").

    Returns:
        Dictionary with nested configuration overrides.
    """
    overrides: dict[str, Any] = {}
    prefix_len = len(prefix)

    # Common field names that contain underscores
    # These should be treated as single field names
    underscore_fields = {
        "base_path",
        "base_url",
        "server_url",
        "method_name",
        "enable_default",
        "reconnect_interval",
    }

    # Known adapter names (to handle http_client, grpc_client, etc.)
    adapter_names = {
        "http_client",
        "grpc_client",
        "websocket_client",
        "mcp_client",
        "nats_client",
    }

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        # Remove prefix and convert to lowercase
        config_key = key[prefix_len:].lower()

        # Split by underscore to create nested path
        parts = config_key.split("_")

        # Check for adapter names in the path
        # e.g., "outbound", "http", "client" -> "outbound", "http_client"
        # Look for patterns: <section>_<adapter_part1>_<adapter_part2>_<field>
        if len(parts) >= 4:
            # Check if parts[1] + "_" + parts[2] forms known adapter
            potential_adapter = "_".join(parts[1:3])
            if potential_adapter in adapter_names:
                # Combine: outbound_http_client_base_url ->
                # outbound, http_client, base_url
                parts = [parts[0]] + [potential_adapter] + parts[3:]

        # Check if the last two parts form a known underscore field
        # If so, combine them
        if len(parts) >= 2:
            last_two = "_".join(parts[-2:])
            if last_two in underscore_fields:
                parts = parts[:-2] + [last_two]

        # Build nested dictionary
        current = overrides
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the final value
        # Try to convert to appropriate type
        final_key = parts[-1]
        try:
            # Try boolean
            if value.lower() in ("true", "false"):
                current[final_key] = value.lower() == "true"
            # Try integer
            elif value.isdigit() or (
                value.startswith("-") and value[1:].isdigit()
            ):
                current[final_key] = int(value)
            # Try float
            elif "." in value and value.replace(".", "").replace(
                "-", ""
            ).isdigit():
                current[final_key] = float(value)
            else:
                current[final_key] = value
        except (ValueError, AttributeError):
            # Fallback to string
            current[final_key] = value

    return overrides


def _merge_config(
    base: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    """Merge configuration overrides into base configuration.

    Args:
        base: Base configuration dictionary.
        overrides: Override dictionary (from environment variables).

    Returns:
        Merged configuration dictionary.
    """
    result = base.copy()

    for key, value in overrides.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            # Recursively merge nested dictionaries
            result[key] = _merge_config(result[key], value)
        else:
            # Override the value
            result[key] = value

    return result


class HexSwitchServiceConfig:
    """Base class for HexSwitch service configuration.

    This class provides a foundation for loading, validating, and transforming
    configuration. Users can extend this class to add custom configuration
    logic.

    Example:
        class MyServiceConfig(HexSwitchServiceConfig):
            def load(self) -> dict[str, Any]:
                # Custom loading logic
                config = super().load()
                # Transform or extend config
                config["custom_field"] = "custom_value"
                return config

            def validate(self, config: dict[str, Any]) -> None:
                # Custom validation
                super().validate(config)
                if "custom_field" not in config:
                    raise ConfigError("custom_field is required")
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize configuration loader.

        Args:
            config_path: Path to configuration file. If None, will try:
                1. Environment variable HEXSWITCH_CONFIG_PATH
                2. Default path (hex-config.toml)
            config: Optional configuration dictionary. If provided,
                config_path is ignored.
        """
        self._config: dict[str, Any] | None = config
        self._config_path: Path | None = None

        if config is not None:
            logger.debug("Using provided configuration dictionary")
        else:
            # Determine config path
            if config_path is None:
                config_path = os.getenv(
                    "HEXSWITCH_CONFIG_PATH", DEFAULT_CONFIG_PATH
                )
            self._config_path = Path(config_path)
            logger.debug("Config path: %s", self._config_path)

    def load(self) -> dict[str, Any]:
        """Load configuration.

        This method can be overridden for custom configuration loading logic.
        By default, it loads from the configured path or uses the provided
        config dict. Environment variables starting with HEX_ are automatically
        loaded and override configuration values. The config is validated and
        transformed before being returned.

        Returns:
            Configuration dictionary (validated and transformed).

        Raises:
            ConfigError: If configuration cannot be loaded or is invalid.
        """
        if self._config is not None:
            # Config was provided in constructor
            logger.debug("Using configuration from constructor")
            config = self._config.copy()
        else:
            if self._config_path is None:
                raise ValueError("No config_path or config provided")

            # Load from file
            logger.info("Loading configuration from: %s", self._config_path)
            config = load_config(self._config_path)

        # Load environment variable overrides
        env_overrides = _load_env_overrides(prefix="HEX_")
        if env_overrides:
            logger.debug(
                "Found %d environment variable override(s) with HEX_ prefix",
                len(env_overrides),
            )
            config = _merge_config(config, env_overrides)

        # Validate and transform
        self.validate(config)
        config = self.transform(config)
        # Note: validate_config() may transform the config (e.g., empty dicts
        # become None), so the returned config may differ from the input
        return config

    def validate(self, config: dict[str, Any]) -> None:
        """Validate configuration.

        This method can be overridden to add custom validation logic.
        By default, it uses the standard HexSwitch validation.

        Args:
            config: Configuration dictionary to validate.

        Raises:
            ConfigError: If validation fails.
        """
        validate_config(config)

    def transform(self, config: dict[str, Any]) -> dict[str, Any]:
        """Transform configuration after loading.

        This method can be overridden to transform or extend the configuration
        after it has been loaded and validated.

        Args:
            config: Configuration dictionary.

        Returns:
            Transformed configuration dictionary.
        """
        return config

    def get_config_path(self) -> Path | None:
        """Get the configuration file path.

        Returns:
            Configuration file path if set, None otherwise.
        """
        return self._config_path


class HexSwitchService:
    """Base class for HexSwitch services with automatic runtime integration.

    This class provides a simple entry point for using the HexSwitch framework.
    By inheriting from HexSwitchService, you automatically get:
    - Runtime initialization and management
    - Configuration loading (automatic with override options)
    - Lifecycle management (start/stop)
    - Signal handlers for graceful shutdown
    - Lifecycle hooks for custom initialization

    Example:
        class MyService(HexSwitchService):
            def on_start(self):
                # Custom initialization before runtime starts
                print("Service starting...")

            def on_ready(self):
                # Called after successful start
                print("Service ready!")

            def on_stop(self):
                # Cleanup
                print("Service stopping...")

        if __name__ == "__main__":
            service = MyService()  # Loads hex-config.toml automatically
            service.run()  # Runs until interrupted

    Example with custom config:
        class MyServiceConfig(HexSwitchServiceConfig):
            def transform(self, config: dict[str, Any]) -> dict[str, Any]:
                # Add custom fields
                config["custom"] = {"enabled": True}
                return config

        class MyService(HexSwitchService):
            def __init__(self):
                super().__init__(config=MyServiceConfig())

        if __name__ == "__main__":
            service = MyService()
            service.run()  # Runs until interrupted
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        config: dict[str, Any] | HexSwitchServiceConfig | None = None,
    ) -> None:
        """Initialize HexSwitchService.

        Args:
            config_path: Path to configuration file. If None, will try:
                1. Environment variable HEXSWITCH_CONFIG_PATH
                2. Default path (hex-config.toml)
            config: Optional configuration dictionary or HexSwitchServiceConfig
                instance. If provided, config_path is ignored.
        """
        self._runtime: Runtime | None = None
        self._config: dict[str, Any] | None = None
        self._config_loader: HexSwitchServiceConfig | None = None
        self._signal_handlers_registered = False

        # If config is a HexSwitchServiceConfig instance
        if isinstance(config, HexSwitchServiceConfig):
            self._config_loader = config
            logger.debug("Using HexSwitchServiceConfig instance")
        elif config is not None:
            # Config dict provided, create a simple config loader
            self._config_loader = HexSwitchServiceConfig(config=config)
            logger.debug("Using provided configuration dictionary")
        else:
            # Create config loader with path
            self._config_loader = HexSwitchServiceConfig(
                config_path=config_path
            )
            logger.debug(
                "Using config path: %s",
                self._config_loader.get_config_path(),
            )

    def load_config(self) -> dict[str, Any]:
        """Load configuration.

        This method delegates to the configured HexSwitchServiceConfig
        instance. It can be overridden for custom configuration loading logic.

        Returns:
            Configuration dictionary.

        Raises:
            ConfigError: If configuration cannot be loaded or is invalid.
        """
        if self._config_loader is None:
            raise ValueError("No config loader configured")

        # Load config (includes validation and transformation)
        config = self._config_loader.load()
        return config

    def start(self) -> None:
        """Start the service.

        This method:
        1. Calls on_start() hook
        2. Loads configuration
        3. Initializes runtime
        4. Starts runtime
        5. Registers signal handlers
        6. Calls on_ready() hook

        Raises:
            RuntimeError: If service fails to start.
        """
        try:
            # Call on_start hook
            self.on_start()

            # Load configuration
            config = self.load_config()
            self._config = config

            # Initialize runtime
            logger.info("Initializing HexSwitch runtime...")
            self._runtime = Runtime(config)

            # Register signal handlers
            self._register_signal_handlers()

            # Start runtime
            logger.info("Starting HexSwitch runtime...")
            self._runtime.start()

            # Call on_ready hook
            self.on_ready()

            logger.info("Service started successfully")
        except Exception as e:
            logger.error("Failed to start service: %s", e)
            raise RuntimeError(f"Service startup failed: {e}") from e

    def stop(self) -> None:
        """Stop the service.

        This method:
        1. Calls on_stop() hook
        2. Stops runtime
        3. Cleans up resources
        """
        try:
            # Call on_stop hook
            self.on_stop()

            # Stop runtime
            if self._runtime is not None:
                logger.info("Stopping HexSwitch runtime...")
                self._runtime.stop()
                self._runtime = None

            logger.info("Service stopped successfully")
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Error during service shutdown: %s", e)

    def is_running(self) -> bool:
        """Check if the service is running.

        Returns:
            True if service is running, False otherwise.
        """
        if self._runtime is None:
            return False

        # Check if runtime has active adapters
        return (
            len(self._runtime.inbound_adapters) > 0
            or len(self._runtime.outbound_adapters) > 0
        )

    def get_runtime(self) -> Runtime | None:
        """Get the runtime instance.

        This allows access to the runtime for advanced usage scenarios.

        Returns:
            Runtime instance if started, None otherwise.
        """
        return self._runtime

    def run(self) -> None:
        """Run the service with standard main loop.

        This method starts the service and runs a standard main loop that
        keeps the service running until interrupted or stopped. It handles
        KeyboardInterrupt gracefully and ensures proper cleanup.

        This is equivalent to:
            service.start()
            try:
                import time
                while service.is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                service.stop()

        Example:
            if __name__ == "__main__":
                service = MyService()
                service.run()  # Runs until interrupted
        """
        self.start()

        try:
            # Service läuft...
            import time
            while self.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def on_start(self) -> None:
        """Hook called before runtime starts.

        Override this method to perform custom initialization
        before the runtime starts.
        """

    def on_ready(self) -> None:
        """Hook called after successful runtime start.

        Override this method to perform actions after the runtime
        has started successfully.
        """

    def on_stop(self) -> None:
        """Hook called before runtime stops.

        Override this method to perform cleanup before the runtime stops.
        """

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown.

        Registers handlers for SIGINT and SIGTERM that will request
        graceful shutdown of the runtime.
        """
        if self._signal_handlers_registered:
            return

        def signal_handler(signum: int, _frame: Any) -> None:
            logger.info("Received signal %s, initiating shutdown...", signum)
            if self._runtime is not None:
                self._runtime.request_shutdown()

        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            self._signal_handlers_registered = True
            logger.debug("Signal handlers registered")
        except (ValueError, OSError) as e:
            # Signal handlers may not be available in all environments
            # (e.g., Windows)
            logger.warning("Could not register signal handlers: %s", e)
