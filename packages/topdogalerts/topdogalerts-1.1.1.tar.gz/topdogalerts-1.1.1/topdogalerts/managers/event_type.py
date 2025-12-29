# topdogalerts/managers/event_type.py
"""
EventType database manager.

Provides functions for fetching and updating event type records.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..db import get_connection
from ..models import EventType

# Row shape from the database
EventTypeRow = Tuple[
    Any,                      # id (uuid)
    Any,                      # source_id (uuid)
    Optional[str],            # name
    Optional[bool],           # listener_healthy
    Optional[Dict[str, Any]], # attribute_schema (jsonb)
    Optional[str],            # trigger_expression (text)
    Optional[Dict[str, Any]], # listener_trigger_map (jsonb)
    Optional[str],            # message_template
]


def fetch_event_type(event_type_id: str) -> EventType:
    """
    Fetch a single EventType record by ID.

    Args:
        event_type_id: The ID of the event type to fetch.

    Returns:
        An EventType object representing the database record.

    Raises:
        LookupError: If no EventType with the given ID exists.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    source_id,
                    name,
                    listener_healthy,
                    attribute_schema,
                    trigger_expression,
                    listener_trigger_map,
                    message_template
                FROM eventtype
                WHERE id = %s
                """,
                (event_type_id,),
            )
            row: Optional[EventTypeRow] = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise LookupError(f"EventType '{event_type_id}' not found.")

    (
        et_id,
        source_id,
        name,
        listener_healthy,
        attribute_schema,
        trigger_expression,
        listener_trigger_map,
        message_template,
    ) = row

    return EventType(
        id=str(et_id),
        source_id=str(source_id),
        name=name,
        listener_healthy=listener_healthy,
        attribute_schema=attribute_schema,
        trigger_expression=trigger_expression,
        listener_trigger_map=listener_trigger_map,
        message_template=message_template,
    )


def set_listener_health(event_type_id: str, is_healthy: bool) -> bool:
    """
    Set the listener_healthy status for an event type.

    Args:
        event_type_id: The ID of the event type to update.
        is_healthy: The new health status.

    Returns:
        The updated health status value.

    Raises:
        LookupError: If no EventType with the given ID exists.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE eventtype
                SET listener_healthy = %s
                WHERE id = %s
                RETURNING listener_healthy
                """,
                (is_healthy, event_type_id),
            )
            row = cur.fetchone()

        if row is None:
            conn.rollback()
            raise LookupError(f"EventType '{event_type_id}' not found.")

        conn.commit()
        return bool(row[0])
    finally:
        conn.close()
