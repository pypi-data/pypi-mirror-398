# topdogalerts/models/event_trigger.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class EventTrigger:
    id: str
    eventtype_id: str

    should_log: Optional[bool]
    enabled: Optional[bool]

    number_value1: Optional[float]
    number_value2: Optional[float]
    number_value3: Optional[float]
    number_value4: Optional[float]

    string_value1: Optional[str]
    string_value2: Optional[str]
    string_value3: Optional[str]
    string_value4: Optional[str]

    datetime_value1: Optional[str]   # ISO 8601 string (for simplicity)
    datetime_value2: Optional[str]