# topdogalerts/models/event_type.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class EventType:
    id: str
    source_id: str
    name: Optional[str]
    listener_healthy: Optional[bool]
    attribute_schema: Optional[Dict[str, Any]]
    trigger_expression: Optional[str]
    listener_trigger_map: Optional[Dict[str, Any]]
    message_template: Optional[str]
