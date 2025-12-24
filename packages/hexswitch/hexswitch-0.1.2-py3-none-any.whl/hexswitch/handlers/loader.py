"""Centralized handler loading logic."""

import importlib
import logging
import threading
from typing import Callable

from hexswitch.ports.exceptions import PortError
from hexswitch.ports.registry import get_port_registry

logger = logging.getLogger(__name__)


class HandlerError(Exception):
    """Raised when handler loading fails."""

    pass


class HandlerLoader:
    """Centralized handler loader with caching and signature validation.

    Handles loading handlers from import paths or port names.
    """

    def __init__(self):
        """Initialize handler loader."""
        self._cache: dict[str, Callable] = {}
        self._lock = threading.Lock()

    def resolve(self, handler_path: str) -> Callable:
        """Resolve handler from import path or port name.

        Args:
            handler_path: "module.path:function_name" or port name

        Returns:
            Handler callable

        Raises:
            HandlerError: If handler cannot be resolved
        """
        # Check cache first
        if handler_path in self._cache:
            return self._cache[handler_path]

        with self._lock:
            # Double-check cache after acquiring lock
            if handler_path in self._cache:
                return self._cache[handler_path]

            # Try as port name first
            try:
                port_registry = get_port_registry()
                # Try to get handler from port
                try:
                    handler = port_registry.get_handler(handler_path)
                    if handler:
                        self._cache[handler_path] = handler
                        logger.debug(f"Loaded handler from port '{handler_path}'")
                        return handler
                except (PortError, AttributeError):
                    # Port doesn't exist or get_handler doesn't exist, continue to import path
                    pass
            except Exception as e:
                logger.debug(f"Failed to load handler from port '{handler_path}': {e}")

            # Try as import path
            if ":" not in handler_path:
                raise HandlerError(
                    f"Invalid handler path: '{handler_path}'. "
                    "Expected format: 'module.path:function_name' or port name"
                )

            module_path, function_name = handler_path.rsplit(":", 1)
            if not module_path or not function_name:
                raise HandlerError(
                    f"Invalid handler path format: '{handler_path}'. "
                    "Module path and function name must not be empty."
                )

            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                raise HandlerError(f"Failed to import module '{module_path}': {e}") from e

            if not hasattr(module, function_name):
                raise HandlerError(f"Module '{module_path}' does not have attribute '{function_name}'")

            handler = getattr(module, function_name)

            if not callable(handler):
                raise HandlerError(f"'{function_name}' in module '{module_path}' is not callable")

            # Validate signature
            self._validate_signature(handler)

            # Cache handler
            self._cache[handler_path] = handler
            logger.debug(f"Loaded handler from import path: '{handler_path}'")

            return handler

    def _validate_signature(self, handler: Callable) -> None:
        """Validate handler signature.

        Args:
            handler: Handler callable to validate

        Raises:
            HandlerError: If signature is invalid
        """
        import inspect

        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())

            # Handler should accept at least one parameter (Envelope)
            if len(params) == 0:
                raise HandlerError(
                    f"Handler '{handler.__name__}' must accept at least one parameter (Envelope)"
                )

            # First parameter should be Envelope (or we accept any type for flexibility)
            # We don't enforce strict type checking here, just that it's callable

        except Exception as e:
            # If signature inspection fails, we still allow it (for flexibility)
            logger.warning(f"Could not validate signature for handler '{handler.__name__}': {e}")

    def load_from_port(self, port_name: str) -> Callable:
        """Load handler from port name.

        Args:
            port_name: Port name

        Returns:
            Handler callable

        Raises:
            HandlerError: If port not found or has no handlers
        """
        port_registry = get_port_registry()

        try:
            # Try to get handler directly
            handler = port_registry.get_handler(port_name)
            if handler:
                self._cache[port_name] = handler
                return handler
            else:
                raise HandlerError(f"Port '{port_name}' has no handlers")

        except PortError as e:
            raise HandlerError(f"Port '{port_name}' not found: {e}") from e
        except AttributeError:
            # get_handler might not exist, try get_port() instead
            try:
                port = port_registry.get_port(port_name)
                if not port:
                    raise HandlerError(f"Port '{port_name}' not found")

                if not port.handlers:
                    raise HandlerError(f"Port '{port_name}' has no handlers")

                # Get first handler
                handler = port.handlers[0]
                self._cache[port_name] = handler
                return handler
            except Exception as e:
                raise HandlerError(f"Failed to load handler from port '{port_name}': {e}") from e

    def cache_handler(self, path: str, handler: Callable) -> None:
        """Cache handler for future use.

        Args:
            path: Handler path (import path or port name)
            handler: Handler callable
        """
        with self._lock:
            self._cache[path] = handler

    def clear_cache(self) -> None:
        """Clear handler cache."""
        with self._lock:
            self._cache.clear()

    def get_cached(self, path: str) -> Callable | None:
        """Get cached handler if available.

        Args:
            path: Handler path

        Returns:
            Cached handler or None
        """
        with self._lock:
            return self._cache.get(path)

