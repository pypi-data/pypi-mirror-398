# topdogalerts/managers/event_trigger.py
"""
EventTrigger database manager.

Provides functions for fetching and updating event trigger records.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, Tuple

from ..db import get_connection
from ..models import EventTrigger

# Row shape from the database
EventTriggerRow = Tuple[
    Any,                # id (uuid)
    Any,                # eventtype_id (uuid)
    Optional[bool],     # should_log
    Optional[bool],     # enabled
    Optional[float],    # number_value1
    Optional[float],    # number_value2
    Optional[float],    # number_value3
    Optional[float],    # number_value4
    Optional[str],      # string_value1
    Optional[str],      # string_value2
    Optional[str],      # string_value3
    Optional[str],      # string_value4
    Optional[datetime], # datetime_value1 (timestamptz)
    Optional[datetime], # datetime_value2
]

# Columns that can be updated via update_event_trigger_column
_ALLOWED_COLUMNS = {
    "enabled",
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


def _datetime_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime object to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat()


def _row_to_event_trigger(row: EventTriggerRow) -> EventTrigger:
    """Convert a database row to an EventTrigger object."""
    (
        et_id,
        eventtype_id,
        should_log,
        enabled,
        number_value1,
        number_value2,
        number_value3,
        number_value4,
        string_value1,
        string_value2,
        string_value3,
        string_value4,
        datetime_value1,
        datetime_value2,
    ) = row

    return EventTrigger(
        id=str(et_id),
        eventtype_id=str(eventtype_id),
        should_log=bool(should_log) if should_log is not None else None,
        enabled=bool(enabled) if enabled is not None else None,
        number_value1=float(number_value1) if number_value1 is not None else None,
        number_value2=float(number_value2) if number_value2 is not None else None,
        number_value3=float(number_value3) if number_value3 is not None else None,
        number_value4=float(number_value4) if number_value4 is not None else None,
        string_value1=string_value1,
        string_value2=string_value2,
        string_value3=string_value3,
        string_value4=string_value4,
        datetime_value1=_datetime_to_iso(datetime_value1),
        datetime_value2=_datetime_to_iso(datetime_value2),
    )


def fetch_event_trigger(event_trigger_id: str) -> EventTrigger:
    """
    Fetch a single EventTrigger by its ID.

    Args:
        event_trigger_id: The ID of the event trigger to fetch.

    Returns:
        An EventTrigger object representing the database record.

    Raises:
        LookupError: If no EventTrigger with the given ID exists.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    eventtype_id,
                    should_log,
                    enabled,
                    number_value1,
                    number_value2,
                    number_value3,
                    number_value4,
                    string_value1,
                    string_value2,
                    string_value3,
                    string_value4,
                    datetime_value1,
                    datetime_value2
                FROM eventtrigger
                WHERE id = %s
                """,
                (event_trigger_id,),
            )
            row: Optional[EventTriggerRow] = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise LookupError(f"EventTrigger '{event_trigger_id}' not found.")

    return _row_to_event_trigger(row)


def fetch_event_triggers_for_eventtype(eventtype_id: str) -> List[EventTrigger]:
    """
    Fetch all EventTriggers for a given EventType ID.

    Args:
        eventtype_id: The ID of the event type to fetch triggers for.

    Returns:
        A list of EventTrigger objects. Empty list if none exist.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    eventtype_id,
                    should_log,
                    enabled,
                    number_value1,
                    number_value2,
                    number_value3,
                    number_value4,
                    string_value1,
                    string_value2,
                    string_value3,
                    string_value4,
                    datetime_value1,
                    datetime_value2
                FROM eventtrigger
                WHERE eventtype_id = %s
                """,
                (eventtype_id,),
            )
            rows: List[EventTriggerRow] = cur.fetchall()
    finally:
        conn.close()

    return [_row_to_event_trigger(row) for row in rows]


def update_event_trigger_column(
    event_trigger_id: str,
    column: str,
    value: Any,
) -> None:
    """
    Update a single column on an EventTrigger record.

    Only certain columns are allowed to be updated for safety:
        - enabled
        - number_value1, number_value2, number_value3, number_value4
        - string_value1, string_value2, string_value3, string_value4
        - datetime_value1, datetime_value2

    Args:
        event_trigger_id: The ID of the event trigger to update.
        column: The column name to update.
        value: The new value for the column.

    Raises:
        ValueError: If the column is not in the allowed list.
        LookupError: If no EventTrigger with the given ID exists.
    """
    if column not in _ALLOWED_COLUMNS:
        raise ValueError(
            f"Column '{column}' is not allowed to be updated. "
            f"Allowed columns: {', '.join(sorted(_ALLOWED_COLUMNS))}"
        )

    # Column name is validated against a whitelist, so safe to interpolate
    sql = f"UPDATE eventtrigger SET {column} = %s WHERE id = %s"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (value, event_trigger_id))
            if cur.rowcount == 0:
                conn.rollback()
                raise LookupError(f"EventTrigger '{event_trigger_id}' not found.")
        conn.commit()
    finally:
        conn.close()
