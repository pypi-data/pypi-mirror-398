"""Adapter runners for unified execution model."""

from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AdapterRunner(ABC):
    """Base class for adapter runners."""

    @abstractmethod
    async def start(self, adapter: Any) -> None:
        """Start adapter in runner context.

        Args:
            adapter: Adapter instance to start
        """
        pass

    @abstractmethod
    async def stop(self, adapter: Any) -> None:
        """Stop adapter gracefully.

        Args:
            adapter: Adapter instance to stop
        """
        pass


class AsyncAdapterRunner(AdapterRunner):
    """Runner for async adapters."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None):
        """Initialize async runner.

        Args:
            loop: Event loop to use (default: current loop or new loop)
        """
        if loop is None:
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in current thread, create a new one
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        else:
            self.loop = loop
        self._tasks: list[asyncio.Task] = []

    async def start(self, adapter: Any) -> None:
        """Start async adapter.

        Args:
            adapter: Adapter instance with async start method
        """
        if hasattr(adapter, "start_async"):
            # Adapter has async start method
            await adapter.start_async()
        elif hasattr(adapter, "start"):
            # Adapter has sync start method, run in executor
            await asyncio.to_thread(adapter.start)
        else:
            raise ValueError(f"Adapter {adapter} has no start method")

    async def stop(self, adapter: Any) -> None:
        """Stop async adapter gracefully.

        Args:
            adapter: Adapter instance
        """
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Stop adapter
        if hasattr(adapter, "stop_async"):
            await adapter.stop_async()
        elif hasattr(adapter, "stop"):
            await asyncio.to_thread(adapter.stop)

    def run_in_background(self, coro: Callable) -> asyncio.Task:
        """Run coroutine in background.

        Args:
            coro: Coroutine to run

        Returns:
            Task handle
        """
        task = self.loop.create_task(coro)
        self._tasks.append(task)
        return task


class BlockingAdapterRunner(AdapterRunner):
    """Runner for blocking adapters using thread pool executor."""

    def __init__(self, executor: ThreadPoolExecutor | None = None):
        """Initialize blocking runner.

        Args:
            executor: Thread pool executor to use (default: creates new one)
        """
        self.executor = executor or ThreadPoolExecutor(max_workers=10)
        self._futures: list[Any] = []

    async def start(self, adapter: Any) -> None:
        """Start blocking adapter in thread pool.

        Args:
            adapter: Adapter instance with blocking start method
        """
        loop = asyncio.get_event_loop()
        # Run adapter.start() in executor (non-blocking for event loop)
        # Note: adapter.start() may start threads/servers that run in background
        future = loop.run_in_executor(self.executor, adapter.start)
        self._futures.append(future)
        # Wait for start to complete (adapter.start() should return quickly
        # after starting background threads/servers)
        await future

    async def stop(self, adapter: Any) -> None:
        """Stop blocking adapter gracefully.

        Args:
            adapter: Adapter instance
        """
        # Wait for all futures to complete
        if self._futures:
            await asyncio.gather(*self._futures, return_exceptions=True)

        # Stop adapter
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, adapter.stop)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown executor.

        Args:
            wait: Whether to wait for pending tasks
        """
        self.executor.shutdown(wait=wait)


