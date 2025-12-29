# topdogalerts/listener/buffering.py
"""
Message buffering infrastructure for topdogalerts listeners.

Provides per-stream message buffering with backpressure support using asyncio.Queue.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BufferConfig:
    """
    Configuration for the message buffer.

    Attributes:
        max_messages_per_stream: Maximum messages to buffer per stream before
            dropping begins. Default is 1000.
        drop_oldest_when_full: If True, drop oldest messages when buffer is full.
            If False, drop newest (incoming) messages. Default is True.
    """

    max_messages_per_stream: int = 1000
    drop_oldest_when_full: bool = True


@dataclass
class BufferedMessage:
    """
    A message stored in the buffer.

    Attributes:
        stream_id: The stream this message belongs to.
        data: The message payload.
    """

    stream_id: str
    data: Dict[str, Any]


class StreamMessageBuffer:
    """
    Per-stream message buffer using asyncio.Queue.

    Provides backpressure handling and organized message storage.
    Each stream (e.g., "BTC-USD" or "btcusdt@kline_1h") gets its own queue.

    This is useful during operations that temporarily disable normal message
    processing (like registry refresh with re-subscription), allowing messages
    to be replayed afterward without data loss.

    Example:
        buffer = StreamMessageBuffer()
        buffer.enable()

        # During operation that needs buffering
        if buffer.is_enabled:
            was_buffered = await buffer.put("BTC-USD", message)

        # After operation completes
        buffer.disable()
        messages_by_stream = await buffer.drain_all()

        # Replay messages
        for stream_id, messages in messages_by_stream.items():
            for msg in messages:
                await process_message(stream_id, msg)
    """

    def __init__(self, config: Optional[BufferConfig] = None) -> None:
        """
        Initialize the buffer.

        Args:
            config: Buffer configuration. Uses defaults if not provided.
        """
        self._config = config or BufferConfig()
        self._enabled = False
        self._queues: Dict[str, asyncio.Queue[Dict[str, Any]]] = {}
        self._message_counts: Dict[str, int] = {}
        self._dropped_counts: Dict[str, int] = {}

    @property
    def is_enabled(self) -> bool:
        """Check if buffering is currently active."""
        return self._enabled

    def enable(self) -> None:
        """
        Start buffering incoming messages.

        Call this before operations that temporarily disable normal processing.
        """
        self._enabled = True

    def disable(self) -> None:
        """
        Stop buffering.

        New messages should be processed directly after calling this.
        Buffered messages remain until drain_all() is called.
        """
        self._enabled = False

    async def put(self, stream_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to the buffer for a specific stream.

        Args:
            stream_id: The stream identifier (e.g., "BTC-USD").
            message: The message data to buffer.

        Returns:
            True if the message was buffered successfully.
            False if the message was dropped due to buffer being full.
        """
        if not self._enabled:
            return False

        # Get or create queue for this stream
        if stream_id not in self._queues:
            self._queues[stream_id] = asyncio.Queue(
                maxsize=self._config.max_messages_per_stream
            )
            self._message_counts[stream_id] = 0
            self._dropped_counts[stream_id] = 0

        queue = self._queues[stream_id]

        # Check if queue is full
        if queue.full():
            if self._config.drop_oldest_when_full:
                # Drop oldest message to make room
                try:
                    queue.get_nowait()
                    self._dropped_counts[stream_id] += 1
                except asyncio.QueueEmpty:
                    pass
            else:
                # Drop this incoming message
                self._dropped_counts[stream_id] += 1
                return False

        try:
            queue.put_nowait(message)
            self._message_counts[stream_id] += 1
            return True
        except asyncio.QueueFull:
            self._dropped_counts[stream_id] += 1
            return False

    async def drain_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Remove and return all buffered messages, organized by stream.

        Returns:
            Dict mapping stream_id to list of messages (in order received).
        """
        result: Dict[str, List[Dict[str, Any]]] = {}

        for stream_id, queue in self._queues.items():
            messages: List[Dict[str, Any]] = []
            while not queue.empty():
                try:
                    msg = queue.get_nowait()
                    messages.append(msg)
                except asyncio.QueueEmpty:
                    break
            if messages:
                result[stream_id] = messages

        # Reset counts after draining
        self._message_counts.clear()

        return result

    def clear(self) -> None:
        """Discard all buffered messages."""
        for queue in self._queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        self._queues.clear()
        self._message_counts.clear()
        self._dropped_counts.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics.

        Returns:
            Dict containing:
                - enabled: Whether buffering is active
                - streams: Number of streams with buffered messages
                - total_buffered: Total messages currently buffered
                - total_dropped: Total messages dropped since last clear
                - by_stream: Per-stream counts
        """
        total_buffered = sum(q.qsize() for q in self._queues.values())
        total_dropped = sum(self._dropped_counts.values())

        by_stream = {
            stream_id: {
                "buffered": self._queues[stream_id].qsize(),
                "dropped": self._dropped_counts.get(stream_id, 0),
            }
            for stream_id in self._queues
        }

        return {
            "enabled": self._enabled,
            "streams": len(self._queues),
            "total_buffered": total_buffered,
            "total_dropped": total_dropped,
            "by_stream": by_stream,
        }
