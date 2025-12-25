# topdogalerts/evaluation/evaluator.py
"""
Trigger evaluation logic for topdogalerts.

Evaluates event attributes against trigger conditions defined in the database.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Mapping, Optional

from ..models import EventTrigger
from ..managers import fetch_event_type, fetch_event_triggers_for_eventtype

# Columns on EventTrigger that event_trigger_map is allowed to reference
_VALID_TRIGGER_VALUE_FIELDS = {
    "number_value1",
    "number_value2",
    "number_value3",
    "number_value4",
    "string_value1",
    "string_value2",
    "string_value3",
    "string_value4",
    "datetime_value1",
    "datetime_value2",
}

# Supported operators for trigger conditions
_SUPPORTED_OPERATORS = {
    "equals",
    "greaterthan",
    "lessthan",
    "greaterthanequals",
    "lessthanequals",
    "between",
}


def evaluate(
    attributes: Mapping[str, Any],
    eventtype_id: str,
) -> List[str]:
    """
    Evaluate an event's attributes against all triggers for the given event type.

    The event_trigger_map in the EventType defines how to evaluate triggers:

        {
          "triggers": [
            {
              "attribute": "asset",
              "operator": "equals",
              "value1": "string_value1",
              "value2": null
            },
            {
              "attribute": "currentLevel",
              "operator": "greaterthanequals",
              "value1": "number_value1",
              "value2": null
            }
          ]
        }

    Supported operators:
        - equals: attribute == trigger value
        - greaterthan: attribute > trigger value
        - lessthan: attribute < trigger value
        - greaterthanequals: attribute >= trigger value
        - lessthanequals: attribute <= trigger value
        - between: value1 <= attribute <= value2

    All conditions in "triggers" are combined with logical AND:
    for a trigger to match, ALL conditions must pass.

    Args:
        attributes: The event attributes to evaluate (matches attribute_schema).
        eventtype_id: The ID of the event type to evaluate against.

    Returns:
        List of trigger IDs (as strings) whose conditions are satisfied.
    """
    # Load the EventType to get its event_trigger_map
    event_type = fetch_event_type(eventtype_id)

    trigger_map_obj: Any = event_type.event_trigger_map or {}

    # Handle case where jsonb was returned as a string
    if isinstance(trigger_map_obj, str):
        try:
            trigger_map_obj = json.loads(trigger_map_obj)
        except Exception:
            trigger_map_obj = {}

    if not isinstance(trigger_map_obj, dict):
        return []

    condition_definitions = trigger_map_obj.get("triggers") or []
    if not isinstance(condition_definitions, list):
        return []

    # Fetch all triggers for this event type
    triggers = fetch_event_triggers_for_eventtype(eventtype_id)

    matching_trigger_ids: List[str] = []

    for trigger in triggers:
        # Skip disabled triggers
        if trigger.enabled is False:
            continue

        if _trigger_matches_event(attributes, trigger, condition_definitions):
            matching_trigger_ids.append(trigger.id)

    return matching_trigger_ids


def _trigger_matches_event(
    attributes: Mapping[str, Any],
    trigger: EventTrigger,
    condition_definitions: List[Mapping[str, Any]],
) -> bool:
    """
    Check if a trigger matches the event attributes.

    All conditions must pass for the trigger to match (logical AND).

    Args:
        attributes: The event attributes to evaluate.
        trigger: The trigger to evaluate against.
        condition_definitions: List of condition definitions from event_trigger_map.

    Returns:
        True if all conditions pass, False otherwise.
    """
    for condition in condition_definitions:
        if not _evaluate_single_condition(attributes, trigger, condition):
            return False
    return True


def _evaluate_single_condition(
    attributes: Mapping[str, Any],
    trigger: EventTrigger,
    condition: Mapping[str, Any],
) -> bool:
    """
    Evaluate a single condition against a trigger.

    Args:
        attributes: The event attributes to evaluate.
        trigger: The trigger to evaluate against.
        condition: A single condition definition containing:
            - attribute: name of the field in attributes
            - operator: one of the supported operators
            - value1: name of the EventTrigger column
            - value2: (optional) second column name for "between" operator

    Returns:
        True if the condition passes, False otherwise.
    """
    attribute_name = condition.get("attribute")
    operator_raw = condition.get("operator")
    column_name1 = condition.get("value1")
    column_name2 = condition.get("value2")

    # Validate required fields
    if not attribute_name or not operator_raw or not column_name1:
        return False

    operator = str(operator_raw).lower()

    # Validate operator
    if operator not in _SUPPORTED_OPERATORS:
        return False

    # Validate column names
    if column_name1 not in _VALID_TRIGGER_VALUE_FIELDS:
        return False

    # "between" requires a valid second column
    if operator == "between":
        if not column_name2 or column_name2 not in _VALID_TRIGGER_VALUE_FIELDS:
            return False

    # Determine value type from column name prefix
    if column_name1.startswith("number_"):
        value_type = "number"
    elif column_name1.startswith("datetime_"):
        value_type = "datetime"
    else:
        value_type = "string"

    # Get raw values
    event_raw_value = attributes.get(attribute_name)
    trigger_raw_value1 = getattr(trigger, column_name1, None)
    trigger_raw_value2 = (
        getattr(trigger, column_name2, None) if operator == "between" else None
    )

    # Convert values based on type
    if value_type == "number":
        event_value = _to_float(event_raw_value)
        trigger_value1 = _to_float(trigger_raw_value1)
        trigger_value2 = (
            _to_float(trigger_raw_value2) if trigger_raw_value2 is not None else None
        )
    elif value_type == "datetime":
        event_value = _to_datetime(event_raw_value)
        trigger_value1 = _to_datetime(trigger_raw_value1)
        trigger_value2 = (
            _to_datetime(trigger_raw_value2) if trigger_raw_value2 is not None else None
        )
    else:
        event_value = None if event_raw_value is None else str(event_raw_value)
        trigger_value1 = None if trigger_raw_value1 is None else str(trigger_raw_value1)
        trigger_value2 = (
            None
            if trigger_raw_value2 is None
            else str(trigger_raw_value2)
            if trigger_raw_value2 is not None
            else None
        )

    # Apply operator
    if operator == "between":
        if event_value is None or trigger_value1 is None or trigger_value2 is None:
            return False
        return _apply_between_operator(event_value, trigger_value1, trigger_value2)
    else:
        if event_value is None or trigger_value1 is None:
            return False
        return _apply_simple_operator(operator, event_value, trigger_value1)


def _to_float(value: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_datetime(value: Any) -> Optional[datetime]:
    """Convert a value to datetime, returning None on failure."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Handle ISO8601 with trailing 'Z'
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _apply_simple_operator(
    operator: str,
    event_value: Any,
    trigger_value: Any,
) -> bool:
    """
    Apply a simple comparison operator.

    Args:
        operator: One of equals, greaterthan, lessthan, greaterthanequals, lessthanequals.
        event_value: The event attribute value.
        trigger_value: The trigger's stored value.

    Returns:
        True if the comparison passes, False otherwise.
    """
    if operator == "equals":
        return event_value == trigger_value
    if operator == "greaterthan":
        return event_value > trigger_value
    if operator == "lessthan":
        return event_value < trigger_value
    if operator == "greaterthanequals":
        return event_value >= trigger_value
    if operator == "lessthanequals":
        return event_value <= trigger_value

    return False


def _apply_between_operator(
    event_value: Any,
    lower_value: Any,
    upper_value: Any,
) -> bool:
    """
    Apply the "between" operator (inclusive on both ends).

    The stored values can be in either order; this function normalizes them.

    Args:
        event_value: The event attribute value.
        lower_value: One boundary value.
        upper_value: The other boundary value.

    Returns:
        True if event_value is between the boundaries (inclusive).
    """
    # Normalize so ordering in DB doesn't matter
    if lower_value <= upper_value:
        min_val, max_val = lower_value, upper_value
    else:
        min_val, max_val = upper_value, lower_value

    return min_val <= event_value <= max_val
