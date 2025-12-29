# topdogalerts/evaluation/evaluator.py
"""
Trigger evaluation logic for topdogalerts.

Evaluates event attributes against trigger conditions defined by boolean
expressions in the database.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping

from ..models import EventTrigger
from ..managers import fetch_event_type, fetch_event_triggers_for_eventtype
from .expression_evaluator import (
    evaluate_expression,
    ExpressionEvaluationError,
)
from .expression_parser import ExpressionParseError

logger = logging.getLogger(__name__)

# Columns on EventTrigger that expressions are allowed to reference
TRIGGER_VALUE_FIELDS = (
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
)


def evaluate(
    attributes: Mapping[str, Any],
    eventtype_id: str,
) -> List[str]:
    """
    Evaluate an event's attributes against all triggers for the given event type.

    The trigger_expression in the EventType defines a boolean expression:

        product == string_value1 AND timeframe == string_value2 AND (
            (string_value3 == "up" AND prev_rsi < number_value1 AND rsi >= number_value1) OR
            (string_value3 == "down" AND prev_rsi > number_value1 AND rsi <= number_value1)
        )

    Variables in the expression can reference:
        - Event attributes: product, timeframe, rsi, prev_rsi, etc.
        - Trigger values: string_value1, number_value1, etc.

    Supported operators:
        - Comparison: ==, !=, <, >, <=, >=
        - Logical: AND, OR, NOT (case-insensitive)
        - Grouping: (, )

    Args:
        attributes: The event attributes to evaluate (matches attribute_schema).
        eventtype_id: The ID of the event type to evaluate against.

    Returns:
        List of trigger IDs (as strings) whose conditions are satisfied.
    """
    # Load the EventType to get its trigger_expression
    event_type = fetch_event_type(eventtype_id)

    trigger_expression = event_type.trigger_expression
    if not trigger_expression:
        logger.warning(
            f"EventType {eventtype_id} has no trigger_expression, skipping evaluation"
        )
        return []

    # Fetch all triggers for this event type
    triggers = fetch_event_triggers_for_eventtype(eventtype_id)

    matching_trigger_ids: List[str] = []

    for trigger in triggers:
        # Skip disabled triggers
        if trigger.enabled is False:
            continue

        if _trigger_matches_event(attributes, trigger, trigger_expression):
            matching_trigger_ids.append(trigger.id)

    return matching_trigger_ids


def _trigger_matches_event(
    attributes: Mapping[str, Any],
    trigger: EventTrigger,
    trigger_expression: str,
) -> bool:
    """
    Check if a trigger matches the event attributes using the expression.

    Args:
        attributes: The event attributes to evaluate.
        trigger: The trigger to evaluate against.
        trigger_expression: The boolean expression from EventType.

    Returns:
        True if the expression evaluates to True, False otherwise.
    """
    # Build trigger values dict from the trigger's value columns
    trigger_values = _build_trigger_values(trigger)

    try:
        return evaluate_expression(
            trigger_expression,
            dict(attributes),
            trigger_values,
        )
    except ExpressionParseError as e:
        # Malformed expression - this is a configuration error
        logger.error(
            f"Expression parse error for trigger {trigger.id}: {e}. "
            f"Expression: {trigger_expression!r}"
        )
        return False
    except ExpressionEvaluationError as e:
        # Evaluation failed - likely a typo in variable name or type mismatch
        logger.error(
            f"Expression evaluation error for trigger {trigger.id}: {e}. "
            f"Attributes: {list(attributes.keys())}, "
            f"Trigger values: {list(trigger_values.keys())}"
        )
        return False
    except Exception as e:
        # Unexpected error
        logger.exception(
            f"Unexpected error evaluating trigger {trigger.id}: {e}. "
            f"Expression: {trigger_expression!r}"
        )
        return False


def _build_trigger_values(trigger: EventTrigger) -> Dict[str, Any]:
    """
    Extract trigger values from an EventTrigger instance.

    Returns a dict with all non-None value fields.
    """
    values: Dict[str, Any] = {}
    for field in TRIGGER_VALUE_FIELDS:
        value = getattr(trigger, field, None)
        if value is not None:
            values[field] = value
    return values
