# topdogalerts/__init__.py
"""
topdogalerts - Event listener infrastructure for cryptocurrency alerts.

This package provides:
    - BaseListener: Abstract base class for building event listeners
    - TriggerRegistry: Registry for managing event triggers
    - Database managers: Functions for fetching/updating records
    - Evaluation: Trigger evaluation logic
    - Publishing: SQS message publishing
    - Models: Data classes for EventType, EventTrigger, Source

Example usage:

    from topdogalerts import (
        BaseListener,
        TriggerRegistry,
        configure_listener_logging,
        evaluate,
        SqsPublisher,
    )

    class MyListener(BaseListener):
        async def _run(self) -> None:
            # Your listener implementation
            ...

    if __name__ == "__main__":
        listener = MyListener()
        listener.start()
"""

# Listener infrastructure
from .listener import (
    BaseListener,
    TriggerRegistry,
    AsyncTriggerNotificationBus,
    StreamMessageBuffer,
    BufferConfig,
    configure_listener_logging,
)

# Publishing
from .publisher import SqsPublisher

# Evaluation
from .evaluation import evaluate

# Database managers
from .managers import (
    fetch_source,
    fetch_event_type,
    fetch_event_trigger,
    fetch_event_triggers_for_eventtype,
    update_event_trigger_column,
    set_listener_health,
)

# Models
from .models import EventType, EventTrigger, Source

__all__ = [
    # Listener infrastructure
    "BaseListener",
    "TriggerRegistry",
    "AsyncTriggerNotificationBus",
    "StreamMessageBuffer",
    "BufferConfig",
    "configure_listener_logging",
    # Publishing
    "SqsPublisher",
    # Evaluation
    "evaluate",
    # Managers
    "fetch_source",
    "fetch_event_type",
    "fetch_event_trigger",
    "fetch_event_triggers_for_eventtype",
    "update_event_trigger_column",
    "set_listener_health",
    # Models
    "EventType",
    "EventTrigger",
    "Source",
]
