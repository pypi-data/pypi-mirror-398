"""Graceful shutdown handling for MCP servers.

This module provides GracefulShutdown class for managing server shutdown
with in-flight request tracking. It ensures that:

1. No new requests are accepted after shutdown is initiated
2. In-flight requests are given time to complete
3. A configurable timeout prevents indefinite waits

Usage:
    shutdown = GracefulShutdown(timeout=30.0)

    # In request handlers:
    async with shutdown.track_request():
        await handle_request()

    # On SIGTERM/SIGINT:
    await shutdown.initiate_shutdown()
    await shutdown.wait_for_shutdown()
"""

import asyncio
import signal
from typing import Set

import structlog

from yirifi_mcp.core.exceptions import GatewayError

logger = structlog.get_logger()


class ShutdownInProgressError(GatewayError):
    """Raised when a request is rejected due to shutdown."""

    def __init__(self):
        super().__init__("Server is shutting down, request rejected")


class GracefulShutdown:
    """Manages graceful shutdown with in-flight request tracking.

    Provides:
    - Request tracking via async context manager
    - Shutdown initiation that stops accepting new requests
    - Waiting for in-flight requests with configurable timeout

    Thread-safe via asyncio primitives.

    Example:
        shutdown = GracefulShutdown(timeout=30.0)

        # Track requests
        async with shutdown.track_request():
            await process_request()

        # On shutdown signal
        await shutdown.initiate_shutdown()
        completed = await shutdown.wait_for_shutdown()
    """

    def __init__(self, timeout: float = 30.0):
        """Initialize shutdown manager.

        Args:
            timeout: Maximum seconds to wait for in-flight requests
        """
        self.timeout = timeout
        self._shutting_down = False
        self._in_flight: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()

    @property
    def is_shutting_down(self) -> bool:
        """Whether shutdown has been initiated."""
        return self._shutting_down

    @property
    def in_flight_count(self) -> int:
        """Number of in-flight requests."""
        return len(self._in_flight)

    async def track_request(self):
        """Context manager to track in-flight requests.

        Raises:
            ShutdownInProgressError: If shutdown has been initiated
        """
        if self._shutting_down:
            raise ShutdownInProgressError()

        task = asyncio.current_task()
        async with self._lock:
            self._in_flight.add(task)

        try:
            yield
        finally:
            async with self._lock:
                self._in_flight.discard(task)
                # If shutting down and no more in-flight, signal completion
                if self._shutting_down and len(self._in_flight) == 0:
                    self._shutdown_event.set()

    async def initiate_shutdown(self) -> None:
        """Begin graceful shutdown.

        After this call:
        - New requests will be rejected with ShutdownInProgressError
        - In-flight requests can continue until completion or timeout
        """
        logger.info(
            "shutdown_initiated",
            in_flight=len(self._in_flight),
        )
        self._shutting_down = True

        # If no in-flight requests, signal immediate completion
        if len(self._in_flight) == 0:
            self._shutdown_event.set()

    async def wait_for_shutdown(self) -> bool:
        """Wait for in-flight requests to complete.

        Blocks until either:
        - All in-flight requests complete
        - Timeout is reached

        Returns:
            True if all requests completed, False if timeout
        """
        if len(self._in_flight) == 0:
            logger.info("shutdown_complete_immediate")
            return True

        logger.info(
            "waiting_for_requests",
            in_flight=len(self._in_flight),
            timeout=self.timeout,
        )

        try:
            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=self.timeout,
            )
            logger.info("shutdown_complete")
            return True
        except asyncio.TimeoutError:
            logger.warning(
                "shutdown_timeout",
                remaining_requests=len(self._in_flight),
            )
            return False

    def reset(self) -> None:
        """Reset shutdown state (for testing)."""
        self._shutting_down = False
        self._in_flight.clear()
        self._shutdown_event.clear()


def setup_signal_handlers(
    shutdown: GracefulShutdown,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    """Set up signal handlers for graceful shutdown.

    Registers handlers for SIGTERM and SIGINT that initiate
    graceful shutdown when received.

    Args:
        shutdown: GracefulShutdown instance to use
        loop: Event loop to add handlers to (default: current loop)
    """
    loop = loop or asyncio.get_event_loop()

    def handle_signal(sig: signal.Signals) -> None:
        logger.info("signal_received", signal=sig.name)
        loop.create_task(shutdown.initiate_shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            logger.debug("signal_handler_not_supported", signal=sig.name)
