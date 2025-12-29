# topdogalerts/listener/registry.py
"""
Trigger registry for managing event triggers.

The TriggerRegistry provides a minimal helper for working with an EventType's
triggers, exposing selector information needed by listeners to determine what
to subscribe to.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Set, Tuple

from ..managers import fetch_event_type, fetch_event_triggers_for_eventtype


class TriggerRegistry:
    """
    Registry for a single EventType's triggers.

    Reads the eventtype.listener_trigger_map for the given event_type_id and
    exposes three things for listeners:

        selector_names:
            Ordered list of selector names, e.g. ["product", "timeframe", "period"]

        selector_to_column_map:
            Mapping from selector name to EventTrigger column name, e.g.
            {
              "product":   "string_value1",
              "timeframe": "string_value2",
              "period":    "number_value2"
            }

        selector_keys:
            List of distinct selector combinations as tuples, in the same order
            as selector_names. Example:

                selector_names = ["product", "timeframe", "period"]
                selector_keys = [
                    ("BTC-USD", "1h", 14.0),
                    ("ETH-USD", "1h", 14.0),
                ]

    Usage:
        registry = TriggerRegistry(event_type_id=1)

        # On startup or periodically:
        registry.refresh()

        for key_tuple in registry.selector_keys:
            # key_tuple follows selector_names order
            product = key_tuple[0]
            timeframe = key_tuple[1]
            period = key_tuple[2]
            ...

    Note:
        Triggers with enabled == False are always ignored.
    """

    def __init__(self, event_type_id: str) -> None:
        """
        Initialize the registry for an event type.

        Args:
            event_type_id: The ID of the event type to manage triggers for.
        """
        self.event_type_id: str = event_type_id

        # Ordered selector names, e.g. ["product", "timeframe", "period"]
        self.selector_names: List[str] = []

        # Mapping from selector name to EventTrigger column name
        self.selector_to_column_map: Dict[str, str] = {}

        # Distinct selector combinations as tuples
        self.selector_keys: List[Tuple[Any, ...]] = []

        # Initial load
        self.refresh()

    def refresh(self) -> None:
        """
        Reload the EventType and its EventTriggers from the database.

        Rebuilds selector_names, selector_to_column_map, and selector_keys.
        Call this periodically (e.g. every N minutes) to pick up new,
        modified, or deleted triggers.
        """
        # Load the event type to get listener_trigger_map
        event_type = fetch_event_type(self.event_type_id)

        # listener_trigger_map is expected to be JSON like:
        # {"product": "string_value1", "timeframe": "string_value2", "period": "number_value2"}
        raw_map = event_type.listener_trigger_map or {}

        if isinstance(raw_map, str):
            try:
                raw_map = json.loads(raw_map)
            except Exception:
                raw_map = {}

        if not isinstance(raw_map, dict):
            raw_map = {}

        selector_to_column_map: Dict[str, str] = {}
        selector_names: List[str] = []

        for selector_name, column_name in raw_map.items():
            if not isinstance(selector_name, str) or not isinstance(column_name, str):
                continue
            selector_to_column_map[selector_name] = column_name
            selector_names.append(selector_name)

        self.selector_to_column_map = selector_to_column_map
        self.selector_names = selector_names

        # Rebuild selector_keys from triggers
        self._rebuild_selector_keys()

    def _rebuild_selector_keys(self) -> None:
        """
        Build selector_keys from the current event triggers.

        Each key is a tuple of values matching the selector_names order.
        Only enabled triggers with all selector values present are included.
        """
        self.selector_keys = []

        if not self.selector_names or not self.selector_to_column_map:
            return

        triggers = fetch_event_triggers_for_eventtype(self.event_type_id)

        keys: Set[Tuple[Any, ...]] = set()

        for trigger in triggers:
            # Skip disabled triggers
            if trigger.enabled is False:
                continue

            key_values: List[Any] = []
            missing_value = False

            for selector_name in self.selector_names:
                column_name = self.selector_to_column_map.get(selector_name)
                if not column_name:
                    missing_value = True
                    break

                value = getattr(trigger, column_name, None)
                if value is None:
                    # Skip triggers missing any selector value
                    missing_value = True
                    break

                key_values.append(value)

            if missing_value:
                continue

            key_tuple = tuple(key_values)
            keys.add(key_tuple)

        self.selector_keys = list(keys)
