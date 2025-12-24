"""Adapter factory for creating adapters from import paths."""

import importlib
from typing import Any

from hexswitch.adapters.base import InboundAdapter, OutboundAdapter
from hexswitch.adapters.exceptions import AdapterError
from hexswitch.registry.adapters import ADAPTER_METADATA


class AdapterFactory:
    """Factory for creating adapter instances from import paths."""

    def __init__(self):
        """Initialize adapter factory."""
        self._registry = ADAPTER_METADATA

    def create_inbound_adapter(self, name: str, config: dict[str, Any]) -> InboundAdapter:
        """Create an inbound adapter instance.

        Args:
            name: Adapter name (e.g., 'http', 'grpc')
            config: Adapter configuration

        Returns:
            InboundAdapter instance

        Raises:
            AdapterError: If adapter cannot be created
        """
        metadata = self._registry.get(name)
        if not metadata:
            raise AdapterError(f"Unknown adapter: {name}")

        impl_path = metadata.get("inbound")
        if not impl_path:
            raise AdapterError(f"Adapter '{name}' does not support inbound direction")

        # Add name to config
        config_with_name = config.copy()
        config_with_name["name"] = name

        adapter = self.create(impl_path, config_with_name)
        if not isinstance(adapter, InboundAdapter):
            raise AdapterError(f"Adapter '{name}' is not an InboundAdapter")
        return adapter

    def create_outbound_adapter(self, name: str, config: dict[str, Any]) -> OutboundAdapter:
        """Create an outbound adapter instance.

        Args:
            name: Adapter name (e.g., 'http_client', 'grpc_client')
            config: Adapter configuration

        Returns:
            OutboundAdapter instance

        Raises:
            AdapterError: If adapter cannot be created
        """
        # Handle names like "http_client" -> "http"
        base_name = name.replace("_client", "")
        metadata = self._registry.get(base_name)
        if not metadata:
            raise AdapterError(f"Unknown adapter: {base_name}")

        impl_path = metadata.get("outbound")
        if not impl_path:
            raise AdapterError(f"Adapter '{base_name}' does not support outbound direction")

        # Add name to config
        config_with_name = config.copy()
        config_with_name["name"] = name

        adapter = self.create(impl_path, config_with_name)
        if not isinstance(adapter, OutboundAdapter):
            raise AdapterError(f"Adapter '{name}' is not an OutboundAdapter")
        return adapter

    @staticmethod
    def create(impl_path: str, cfg: dict[str, Any]) -> InboundAdapter | OutboundAdapter:
        """Create adapter from import path.

        Args:
            impl_path: Module path like "hexswitch.adapters.http:HttpAdapterServer"
            cfg: Adapter configuration dictionary

        Returns:
            Adapter instance

        Raises:
            AdapterError: If adapter cannot be created
        """
        if ":" not in impl_path:
            raise AdapterError(f"Invalid adapter path format: {impl_path}. Expected 'module.path:ClassName'")

        try:
            module_path, class_name = impl_path.rsplit(":", 1)
            if not module_path or not class_name:
                raise AdapterError(
                    f"Invalid adapter path format: {impl_path}. Module path and class name must not be empty."
                )

            # Import module
            module = importlib.import_module(module_path)

            # Get adapter class
            if not hasattr(module, class_name):
                raise AdapterError(f"Module '{module_path}' does not have class '{class_name}'")

            adapter_class = getattr(module, class_name)

            # Verify it's an adapter class
            if not issubclass(adapter_class, (InboundAdapter, OutboundAdapter)):
                raise AdapterError(f"Class '{class_name}' is not an adapter (InboundAdapter or OutboundAdapter)")

            # Create adapter instance
            # Extract name from config or use default
            adapter_name = cfg.get("name", "")
            if not adapter_name:
                # Try to infer name from class name
                adapter_name = class_name.lower().replace("adapter", "").replace("server", "").replace("client", "")

            return adapter_class(name=adapter_name, config=cfg)

        except ImportError as e:
            raise AdapterError(f"Failed to import module for adapter '{impl_path}': {e}") from e
        except AttributeError as e:
            raise AdapterError(f"Failed to get adapter class from '{impl_path}': {e}") from e
        except Exception as e:
            raise AdapterError(f"Failed to create adapter from '{impl_path}': {e}") from e

