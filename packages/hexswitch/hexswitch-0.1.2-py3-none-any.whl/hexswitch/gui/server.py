"""GUI server for HexSwitch framework."""

import asyncio
import logging
import threading
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from hexswitch.gui.routes import router

logger = logging.getLogger(__name__)


class GuiServer:
    """GUI server for HexSwitch framework."""

    def __init__(self, config: dict[str, Any], runtime: Any | None = None):
        """Initialize GUI server.

        Args:
            config: GUI configuration dictionary.
            runtime: Optional Runtime instance for adapter status.
        """
        self.config = config
        self.runtime = runtime
        self.port = config.get("port", 8080)
        self.enabled = config.get("enabled", True)
        self._running = False
        self._app: FastAPI | None = None
        self._server: uvicorn.Server | None = None
        self._server_thread: threading.Thread | None = None
        self._loop: Any | None = None

    def _create_app(self) -> FastAPI:
        """Create FastAPI application.

        Returns:
            FastAPI application instance.
        """
        app = FastAPI(title="HexSwitch GUI", version="0.1.2")

        # Store runtime in app state for access in routes
        if self.runtime:
            app.state.runtime = self.runtime

        # Include API routes (after setting app state)
        app.include_router(router)

        # Try to mount static files if directory exists
        try:
            import os
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            if os.path.exists(static_dir):
                app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
        except Exception as e:
            logger.warning(f"Could not mount static files: {e}")

        return app

    def start(self) -> None:
        """Start the GUI server.

        Raises:
            RuntimeError: If server fails to start.
        """
        if not self.enabled:
            logger.info("GUI server is disabled")
            return

        if self._running:
            logger.warning("GUI server is already running")
            return

        try:
            self._app = self._create_app()

            config = uvicorn.Config(
                self._app, host="0.0.0.0", port=self.port, log_level="info"
            )
            self._server = uvicorn.Server(config)

            # Start server in background thread
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            loop.create_task(self._server.serve())

            def run_server():
                loop.run_forever()

            self._server_thread = threading.Thread(target=run_server, daemon=True)
            self._server_thread.start()
            self._running = True

            logger.info(f"GUI server started on port {self.port}")
        except Exception as e:
            raise RuntimeError(f"Failed to start GUI server: {e}") from e

    def stop(self) -> None:
        """Stop the GUI server."""
        if not self._running:
            logger.warning("GUI server is not running")
            return

        try:
            if self._server:
                self._server.should_exit = True

            if self._loop:
                if self._loop.is_running():
                    # Stop the loop if it's running
                    self._loop.call_soon_threadsafe(self._loop.stop)
                elif not self._loop.is_closed():
                    # If loop exists but is not running, close it
                    try:
                        # Cancel any pending tasks
                        pending = asyncio.all_tasks(self._loop)
                        for task in pending:
                            task.cancel()
                        # Wait for tasks to be cancelled
                        if pending:
                            self._loop.run_until_complete(
                                asyncio.gather(*pending, return_exceptions=True)
                            )
                    except Exception:
                        pass
                    finally:
                        if not self._loop.is_closed():
                            self._loop.close()

            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=5.0)

            self._running = False
            self._loop = None
            self._server = None
            self._app = None
            logger.info("GUI server stopped")
        except Exception as e:
            logger.error(f"Error stopping GUI server: {e}")
            # Ensure state is reset even on error
            self._running = False
            self._loop = None

