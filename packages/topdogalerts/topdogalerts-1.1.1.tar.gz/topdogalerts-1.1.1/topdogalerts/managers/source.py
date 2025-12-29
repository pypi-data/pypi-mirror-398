# topdogalerts/managers/source.py
"""
Source database manager.

Provides functions for fetching source records from the database.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

from ..db import get_connection
from ..models import Source

# Row shape: (id, name, access)
SourceRow = Tuple[Any, str, str]


def fetch_source(source_id: str) -> Source:
    """
    Fetch a source record by ID.

    Args:
        source_id: The ID of the source to fetch.

    Returns:
        A Source object representing the database record.

    Raises:
        LookupError: If the source is not found.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, access
                FROM source
                WHERE id = %s
                """,
                (source_id,),
            )
            row: Optional[SourceRow] = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise LookupError(f"Source '{source_id}' not found.")

    source_id_db, name, access = row

    return Source(
        id=str(source_id_db),
        name=name,
        access=access,
    )
