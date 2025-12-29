"""Store log events in pgvector."""

import numpy as np
from psycopg2.extras import Json, execute_values

from .db import get_cursor


def insert_event(
    raw_log: dict,
    raw_text: str,
    iocs: dict,
    embedding: np.ndarray,
    source_file: str
) -> int:
    """Insert a single log event. Returns the event ID."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO log_events (raw_log, raw_text, iocs, embedding, source_file)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (Json(raw_log), raw_text, Json(iocs), embedding.tolist(), source_file)
        )
        return cur.fetchone()[0]


def insert_batch(
    records: list[tuple[dict, str, dict, np.ndarray, str]]
) -> int:
    """Insert a batch of log events.

    Each record is (raw_log, raw_text, iocs, embedding, source_file).
    Returns the number of inserted records.
    """
    if not records:
        return 0

    with get_cursor() as cur:
        # Prepare data for execute_values
        data = [
            (Json(raw_log), raw_text, Json(iocs), emb.tolist(), source_file)
            for raw_log, raw_text, iocs, emb, source_file in records
        ]

        execute_values(
            cur,
            """
            INSERT INTO log_events (raw_log, raw_text, iocs, embedding, source_file)
            VALUES %s
            """,
            data,
            template="(%s, %s, %s, %s, %s)"
        )

        return len(records)


def get_event_count() -> int:
    """Get total number of events in the database."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM log_events")
        return cur.fetchone()[0]
