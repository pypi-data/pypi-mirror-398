# topdogalerts/listener/__init__.py
"""
Listener infrastructure for topdogalerts.

Provides base classes and utilities for building event listeners.
"""
from .base import BaseListener
from .registry import TriggerRegistry
from .notifications import AsyncTriggerNotificationBus
from .buffering import StreamMessageBuffer, BufferConfig
from .logging import configure_listener_logging

__all__ = [
    "BaseListener",
    "TriggerRegistry",
    "AsyncTriggerNotificationBus",
    "StreamMessageBuffer",
    "BufferConfig",
    "configure_listener_logging",
]
