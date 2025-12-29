# topdogalerts/listener/base.py
"""
Abstract base class for topdogalerts listeners.

Provides common infrastructure while remaining transport-agnostic.
Subclasses handle their own connection mechanism (WebSocket, HTTP polling, Pub/Sub, etc.).

Uses push-based PostgreSQL LISTEN/NOTIFY for real-time trigger updates
instead of polling the database.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import signal
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple

from .registry import TriggerRegistry
from .notifications import AsyncTriggerNotificationBus
from .buffering import StreamMessageBuffer, BufferConfig
from ..evaluation import evaluate, validate_expression
from ..managers import set_listener_health, fetch_event_type
from ..publisher import SqsPublisher


class BaseListener(ABC):
    """
    Abstract base class providing common infrastructure for all listeners.

    This class is TRANSPORT-AGNOSTIC. Subclasses are responsible for:
        - Connecting to their data source (WebSocket, HTTP, Pub/Sub, etc.)
        - Receiving and parsing messages
        - Calling provided helper methods for evaluation and publishing

    Provided infrastructure:
        - Registry management: _init_registries(), _refresh_registries()
        - Health reporting: _set_health_status()
        - Trigger evaluation: _evaluate_and_publish()
        - Signal handling: start() with graceful shutdown
        - Optional message buffering: _enable_buffering(), _buffer_message(), etc.
        - Push-based trigger notifications (enabled by default)
        - Logging utilities: _fmt_set(), _now_iso()

    Required overrides:
        - _run(): Main async loop (your connection and message handling)

    Required overrides for push-based trigger updates:
        - _on_trigger_change(): Called when triggers are added/modified/deleted

        Example subclass:

            class MyListener(BaseListener):
                def __init__(self) -> None:
                    super().__init__(
                    eventtype_ids=["<eventtype-uuid-1>", "<eventtype-uuid-2>"],
                    listener_name="my_listener",
                    logger=configure_listener_logging("my_listener"),
                )
                # Your custom state here
                self._websocket = None

            async def _run(self) -> None:
                while not self._shutdown_requested.is_set():
                    # Your connection and message handling logic
                    ...

            async def _on_trigger_change(self, payload: Dict[str, Any]) -> None:
                # Handle subscription changes when triggers are modified
                ...
    """

    def __init__(
        self,
        eventtype_ids: List[str],
        listener_name: str,
        logger: logging.Logger,
        buffer_config: Optional[BufferConfig] = None,
    ) -> None:
        """
        Initialize the base listener.

        Args:
            eventtype_ids: List of event type IDs this listener handles.
            listener_name: Human-readable name for logging.
            logger: Configured logger instance.
            buffer_config: Optional configuration for message buffering.
        """
        self.eventtype_ids = eventtype_ids
        self.listener_name = listener_name
        self.logger = logger

        # Registry management: one registry per event type
        self.registries: Dict[str, Optional[TriggerRegistry]] = {}

        # Concurrency control for registry access
        self._registry_lock = asyncio.Lock()

        # SQS publisher for alert messages
        self.publisher = SqsPublisher()

        # Graceful shutdown coordination
        self._shutdown_requested = asyncio.Event()

        # Optional message buffer (disabled by default)
        self._message_buffer: Optional[StreamMessageBuffer] = None
        if buffer_config is not None:
            self._message_buffer = StreamMessageBuffer(buffer_config)

        # Push-based trigger change notifications
        self._notification_bus: Optional[AsyncTriggerNotificationBus] = None

    # -------------------------------------------------------------------------
    # Registry Management
    # -------------------------------------------------------------------------

    def _init_registries(self) -> None:
        """
        Initialize trigger registries for all configured event types.

        Creates a TriggerRegistry for each event type ID, loading triggers
        from the database. Failed initializations result in None entries.

        Also validates trigger expressions at startup to catch configuration
        errors early.
        """
        for eventtype_id in self.eventtype_ids:
            try:
                registry = TriggerRegistry(eventtype_id)
                self.registries[eventtype_id] = registry
                self.logger.info(f"Initialized registry for EventType {eventtype_id}")
                self.logger.debug(
                    f"EventType {eventtype_id} selector_names={registry.selector_names}"
                )
                self.logger.debug(
                    f"EventType {eventtype_id} selector_keys_count={len(registry.selector_keys)}"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to init registry for EventType {eventtype_id}: {e}"
                )
                self.registries[eventtype_id] = None

        # Validate trigger expressions for all event types
        self._validate_expressions()

    def _validate_expressions(self) -> None:
        """
        Validate trigger expressions for all event types at startup.

        Logs errors for any invalid expressions. This catches configuration
        errors early rather than silently failing during evaluation.
        """
        for eventtype_id in self.eventtype_ids:
            try:
                event_type = fetch_event_type(eventtype_id)
                expression = event_type.trigger_expression

                if not expression:
                    self.logger.warning(
                        f"EventType {eventtype_id} ({event_type.name}) has no "
                        "trigger_expression configured"
                    )
                    continue

                error = validate_expression(expression)
                if error:
                    self.logger.error(
                        f"Invalid trigger_expression for EventType {eventtype_id} "
                        f"({event_type.name}): {error}"
                    )
                else:
                    self.logger.info(
                        f"Validated trigger_expression for EventType {eventtype_id} "
                        f"({event_type.name})"
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to validate expression for EventType {eventtype_id}: {e}"
                )

    async def _refresh_registries(self) -> None:
        """
        Refresh all registries from the database.

        Call this when a trigger change notification is received.
        Uses the registry lock to prevent concurrent modifications.
        """
        async with self._registry_lock:
            for eventtype_id, registry in self.registries.items():
                if registry is not None:
                    try:
                        # Run blocking refresh in thread pool
                        await asyncio.to_thread(registry.refresh)
                        self.logger.debug(
                            f"Refreshed registry for EventType {eventtype_id}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to refresh registry {eventtype_id}: {e}"
                        )

    def _get_all_selector_keys(self) -> Set[Tuple[Any, ...]]:
        """
        Get all unique selector keys across all registries.

        Returns:
            Set of selector tuples from all initialized registries.
        """
        all_keys: Set[Tuple[Any, ...]] = set()
        for registry in self.registries.values():
            if registry is not None:
                all_keys.update(registry.selector_keys)
        return all_keys

    # -------------------------------------------------------------------------
    # Health Status
    # -------------------------------------------------------------------------

    def _set_health_status(self, is_healthy: bool) -> None:
        """
        Update health status for all event types this listener handles.

        Args:
            is_healthy: True if the listener is healthy and processing,
                       False if disconnected or experiencing errors.
        """
        for eventtype_id in self.eventtype_ids:
            try:
                set_listener_health(eventtype_id, is_healthy)
            except Exception as e:
                self.logger.error(
                    f"Failed to set health status for EventType {eventtype_id}: {e}"
                )

    # -------------------------------------------------------------------------
    # Trigger Evaluation and Publishing
    # -------------------------------------------------------------------------

    async def _evaluate_and_publish(
        self,
        eventtype_id: str,
        attributes: Dict[str, Any],
        log_context: str = "",
    ) -> List[str]:
        """
        Evaluate triggers and publish matches to SQS.

        This is the main method for processing events. It:
        1. Runs evaluate() against all triggers for the event type
        2. Publishes a message to SQS for each matching trigger

        Args:
            eventtype_id: The event type to evaluate against.
            attributes: Event attributes to match against triggers.
            log_context: Optional context string for log messages.

        Returns:
            List of trigger IDs that fired.
        """
        try:
            # Run blocking evaluate() in thread pool to avoid blocking event loop
            matching_ids = await asyncio.to_thread(evaluate, attributes, eventtype_id)
            self.logger.debug(
                f"Evaluation complete: eventtype={eventtype_id} "
                f"context={log_context} matches={len(matching_ids)}"
            )
        except Exception as e:
            self.logger.error(f"Evaluation failed for EventType {eventtype_id}: {e}")
            return []

        if not matching_ids:
            return []

        # Publish to SQS for each matching trigger
        for trigger_id in matching_ids:
            self.logger.info(
                f"TRIGGER FIRED: {log_context} [trigger_id={trigger_id}]"
            )

            try:
                message = {"trigger_id": trigger_id, "attributes": attributes}
                # Run blocking publish() in thread pool
                message_id = await asyncio.to_thread(self.publisher.publish, message)
                self.logger.info(f"Published to SQS (message_id={message_id})")
            except Exception as e:
                self.logger.error(f"Failed to publish trigger {trigger_id}: {e}")

        return matching_ids

    # -------------------------------------------------------------------------
    # Push-Based Trigger Notifications 
    # -------------------------------------------------------------------------

    async def _start_trigger_notifications(self) -> None:
        """
        Start listening for trigger change notifications from the database.

        Uses PostgreSQL LISTEN/NOTIFY for real-time trigger updates.
        When a trigger changes, _handle_trigger_notification() is called.
        """
        self._notification_bus = AsyncTriggerNotificationBus()
        self._notification_bus.add_callback(self._handle_trigger_notification)

        # Connect notification health to listener health
        self._notification_bus.set_health_callback(self._on_notification_health_change)

        await self._notification_bus.start()
        self.logger.info("Push-based trigger notifications started")

    def _on_notification_health_change(self, is_healthy: bool) -> None:
        """
        Handle notification bus health status changes.

        Called when the notification bus connects successfully (True) or
        fails to connect after multiple retries (False).

        Args:
            is_healthy: True if notification bus is healthy, False otherwise.
        """
        if not is_healthy:
            self.logger.error(
                "Trigger notification bus unhealthy (multiple connection failures), "
                "marking listener unhealthy"
            )
            self._set_health_status(False)

    async def _stop_trigger_notifications(self) -> None:
        """Stop listening for trigger change notifications."""
        if self._notification_bus:
            await self._notification_bus.stop()
            self._notification_bus = None
            self.logger.info("Push-based trigger notifications stopped")

    async def _handle_trigger_notification(self, payload: Dict[str, Any]) -> None:
        """
        Handle a trigger change notification from the database.

        Called when a trigger is added, modified, or deleted.
        Refreshes affected registries and calls _on_trigger_change() hook.

        Args:
            payload: Notification payload containing:
                - operation: INSERT, UPDATE, or DELETE
                - eventtype_id: The affected event type
                - trigger_id: The affected trigger ID
                - enabled: Current enabled status (false for DELETE)
        """
        eventtype_id = payload.get("eventtype_id")
        operation = payload.get("operation", "UNKNOWN")

        # Ignore notifications for event types this listener doesn't handle
        if eventtype_id not in self.eventtype_ids:
            self.logger.debug(
                f"Ignoring trigger notification for unrelated eventtype={eventtype_id} "
                f"trigger={payload.get('trigger_id')}"
            )
            return

        self.logger.info(
            f"Trigger notification: {operation} "
            f"eventtype={eventtype_id} trigger={payload.get('trigger_id')}"
        )

        await self._refresh_registries()
        await self._on_trigger_change(payload)

    @abstractmethod
    async def _on_trigger_change(self, payload: Dict[str, Any]) -> None:
        """
        Hook called after triggers change. Subclass MUST implement.

        This is called whenever a trigger for one of our event types is
        added, modified, or deleted. Subclasses should:
            - Update WebSocket subscriptions
            - Adjust state tracking
            - Seed new data sources

        Args:
            payload: The trigger change notification payload.
        """
        pass

    # -------------------------------------------------------------------------
    # Message Buffering (Optional)
    # -------------------------------------------------------------------------

    def _enable_buffering(self) -> None:
        """
        Enable message buffering.

        Call this before operations that temporarily disable normal processing
        (like subscription changes during trigger updates).
        """
        if self._message_buffer:
            self._message_buffer.enable()
            self.logger.debug("Message buffering enabled")

    def _disable_buffering(self) -> None:
        """
        Disable buffering and return control to normal processing.

        After calling this, use _replay_buffered_messages() to process
        any messages that were buffered.
        """
        if self._message_buffer:
            self._message_buffer.disable()
            self.logger.debug("Message buffering disabled")

    async def _buffer_message(self, stream_id: str, message: Dict[str, Any]) -> bool:
        """
        Buffer a message if buffering is enabled.

        Args:
            stream_id: The stream this message belongs to.
            message: The message data to buffer.

        Returns:
            True if the message was buffered, False if buffering is disabled
            or the message was dropped.
        """
        if self._message_buffer and self._message_buffer.is_enabled:
            was_buffered = await self._message_buffer.put(stream_id, message)
            if was_buffered:
                self.logger.debug(
                    f"Buffered message for stream {stream_id}"
                )
            return was_buffered
        return False

    async def _replay_buffered_messages(
        self,
        handler: Callable[[str, Dict[str, Any]], Awaitable[None]],
    ) -> int:
        """
        Replay all buffered messages through the provided handler.

        Args:
            handler: Async function to process each message.
                    Takes (stream_id, message) as arguments.

        Returns:
            Number of messages replayed.
        """
        if not self._message_buffer:
            return 0

        messages_by_stream = await self._message_buffer.drain_all()
        total_replayed = 0

        for stream_id, messages in messages_by_stream.items():
            for message in messages:
                try:
                    await handler(stream_id, message)
                    total_replayed += 1
                except Exception as e:
                    self.logger.error(
                        f"Error replaying buffered message for {stream_id}: {e}"
                    )

        if total_replayed > 0:
            self.logger.info(f"Replayed {total_replayed} buffered messages")

        return total_replayed

    # -------------------------------------------------------------------------
    # Logging Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _fmt_set(values: Set[str], max_items: int = 25) -> str:
        """
        Format a set for logging, truncating if too large.

        Args:
            values: The set of strings to format.
            max_items: Maximum items to show before truncating.

        Returns:
            Formatted string like "[a, b, c]" or "[a, b, ... (+5 more)]".
        """
        if not values:
            return "[]"
        items = sorted(values)
        if len(items) <= max_items:
            return "[" + ", ".join(items) + "]"
        head = items[:max_items]
        return "[" + ", ".join(head) + f", ... (+{len(items) - max_items} more)]"

    @staticmethod
    def _now_iso() -> str:
        """
        Get current UTC time as ISO 8601 string.

        Returns:
            Formatted string like "2025-01-15T12:30:45Z".
        """
        return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # -------------------------------------------------------------------------
    # Lifecycle Management
    # -------------------------------------------------------------------------

    @abstractmethod
    async def _run(self) -> None:
        """
        Main listener loop. Subclass MUST implement.

        This method should:
        1. Connect to the data source
        2. Process incoming messages
        3. Handle reconnection as needed
        4. Check self._shutdown_requested.is_set() to support graceful shutdown

        The base class handles:
        - Signal registration (SIGTERM, SIGINT)
        - Health status on start/stop
        - Push-based trigger notifications (started automatically)

        Example implementation:

            async def _run(self) -> None:
                while not self._shutdown_requested.is_set():
                    try:
                        self._init_registries()
                        async with websockets.connect(WS_URL) as ws:
                            self._set_health_status(True)
                            async for message in ws:
                                if self._shutdown_requested.is_set():
                                    break
                                await self._process_message(json.loads(message))
                    except Exception as e:
                        self.logger.error(f"Connection error: {e}")
                        self._set_health_status(False)
                        await asyncio.sleep(5)
        """
        pass

    async def _run_with_signal_handling(self) -> None:
        """
        Run the main loop with signal handling and trigger notifications.

        Sets up SIGTERM and SIGINT handlers for graceful shutdown,
        starts push-based trigger notifications, then runs _run()
        until completion or shutdown.
        """
        loop = asyncio.get_running_loop()

        def signal_handler(sig: signal.Signals) -> None:
            self.logger.info(
                f"Received signal {sig.name}, initiating graceful shutdown..."
            )
            self._shutdown_requested.set()

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler, sig)

        try:
            # Start push-based trigger notifications
            await self._start_trigger_notifications()

            # Run the main listener loop
            await self._run()
        finally:
            # Stop trigger notifications
            await self._stop_trigger_notifications()

            # Remove signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.remove_signal_handler(sig)

    def start(self) -> None:
        """
        Start the listener (blocking).

        Sets up signal handlers, starts trigger notifications,
        runs the main loop, and handles graceful shutdown.
        This is the main entry point for running a listener.
        """
        self.logger.info(f"Starting {self.listener_name} listener...")
        try:
            asyncio.run(self._run_with_signal_handling())
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested via KeyboardInterrupt")
        finally:
            self._set_health_status(False)
            self.logger.info(f"{self.listener_name} listener stopped")
