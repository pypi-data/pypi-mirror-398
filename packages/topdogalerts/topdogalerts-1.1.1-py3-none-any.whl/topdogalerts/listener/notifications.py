# topdogalerts/listener/notifications.py
"""
Push-based trigger change notifications using PostgreSQL LISTEN/NOTIFY.

Provides async-native notification handling using asyncpg.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default max consecutive failures before marking unhealthy
DEFAULT_MAX_CONSECUTIVE_FAILURES = 3


class AsyncTriggerNotificationBus:
    """
    Async PostgreSQL LISTEN/NOTIFY client for trigger change notifications.

    Connects to PostgreSQL using asyncpg and listens for trigger changes.
    When a notification arrives, all registered callbacks are invoked.

    Features:
        - Automatic reconnection on connection loss
        - Async-native (integrates with asyncio event loop)
        - Multiple callback support
        - Graceful shutdown

    Expected notification payload shape (from database trigger function):
        {
            "operation": "INSERT" | "UPDATE" | "DELETE",
            "eventtype_id": "<uuid>",
            "trigger_id": "<uuid>",
            "enabled": true
        }

    Example:
        bus = AsyncTriggerNotificationBus()

        async def on_trigger_change(payload: Dict[str, Any]) -> None:
            print(f"Trigger changed: {payload}")

        bus.add_callback(on_trigger_change)
        await bus.start()

        # ... later
        await bus.stop()
    """

    def __init__(
        self,
        channel: str = "eventtrigger_changed",
        reconnect_delay: float = 5.0,
        max_consecutive_failures: int = DEFAULT_MAX_CONSECUTIVE_FAILURES,
    ) -> None:
        """
        Initialize the notification bus.

        Args:
            channel: The PostgreSQL NOTIFY channel to listen on.
            reconnect_delay: Seconds to wait before reconnecting after disconnection.
            max_consecutive_failures: Number of consecutive failures before marking unhealthy.
        """
        self.channel = channel
        self.reconnect_delay = reconnect_delay
        self._max_consecutive_failures = max_consecutive_failures

        self._callbacks: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._connection: Optional[Any] = None  # asyncpg.Connection
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None

        # Health tracking
        self._consecutive_failures = 0
        self._health_callback: Optional[Callable[[bool], None]] = None

    def add_callback(
        self, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Register a callback to be invoked when notifications arrive.

        Args:
            callback: An async function that takes a payload dict as argument.
        """
        self._callbacks.append(callback)

    def remove_callback(
        self, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Remove a previously registered callback.

        Args:
            callback: The callback function to remove.
        """
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    def set_health_callback(self, callback: Callable[[bool], None]) -> None:
        """
        Set a callback to be invoked when health status changes.

        The callback receives True when connection is established successfully,
        and False when consecutive failures exceed the threshold.

        Args:
            callback: A function that takes a boolean health status.
        """
        self._health_callback = callback

    async def start(self) -> None:
        """
        Connect to PostgreSQL and start listening for notifications.

        This starts a background task that maintains the connection and
        dispatches notifications to callbacks.
        """
        if self._running:
            return

        self._running = True
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info(f"AsyncTriggerNotificationBus started, listening on '{self.channel}'")

    async def stop(self) -> None:
        """
        Stop listening and close the connection.

        Waits for the listen task to complete gracefully.
        """
        self._running = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        await self._close_connection()
        logger.info("AsyncTriggerNotificationBus stopped")

    async def _listen_loop(self) -> None:
        """
        Main listen loop with automatic reconnection.

        Maintains a connection to PostgreSQL and dispatches notifications
        to registered callbacks. Reconnects automatically on connection loss.
        Tracks consecutive failures and invokes health callback when threshold is exceeded.
        """
        # Import asyncpg here to avoid making it a hard dependency
        # for code that doesn't use notifications
        try:
            import asyncpg
        except ImportError:
            logger.error(
                "asyncpg is required for AsyncTriggerNotificationBus. "
                "Install it with: pip install asyncpg"
            )
            return

        from ..db import get_async_connection_string

        while self._running:
            try:
                connection_string = get_async_connection_string()
                self._connection = await asyncpg.connect(connection_string)

                # Reset failure count on successful connect
                self._consecutive_failures = 0
                if self._health_callback:
                    self._health_callback(True)

                logger.info(f"Connected to PostgreSQL, listening on '{self.channel}'")

                # Add notification listener
                await self._connection.add_listener(
                    self.channel, self._notification_handler
                )

                # Keep connection alive until stopped or disconnected
                while self._running:
                    # Periodic check to ensure connection is still alive
                    try:
                        await self._connection.execute("SELECT 1")
                    except Exception:
                        logger.warning("Connection check failed, will reconnect")
                        break

                    await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_failures += 1
                logger.error(
                    f"Notification bus error (attempt {self._consecutive_failures}/"
                    f"{self._max_consecutive_failures}): {e}"
                )

                # Mark unhealthy after max consecutive failures
                if self._consecutive_failures >= self._max_consecutive_failures:
                    logger.critical(
                        f"Notification bus failed {self._consecutive_failures} consecutive times, "
                        "marking as unhealthy"
                    )
                    if self._health_callback:
                        self._health_callback(False)

            await self._close_connection()

            if self._running:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)

    def _notification_handler(
        self,
        connection: Any,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        """
        Handle incoming PostgreSQL notifications.

        This is called synchronously by asyncpg, so we schedule async
        callback dispatch on the event loop.
        """
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in notification payload: {payload}")
            data = {}

        # Schedule async dispatch
        asyncio.create_task(self._dispatch(data))

    async def _dispatch(self, payload: Dict[str, Any]) -> None:
        """
        Dispatch a notification to all registered callbacks.

        Args:
            payload: The parsed notification payload.
        """
        for callback in self._callbacks:
            try:
                await callback(payload)
            except Exception as e:
                logger.error(f"Callback error in notification handler: {e}")

    async def _close_connection(self) -> None:
        """Close the database connection if open."""
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None
