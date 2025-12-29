"""Database connection and schema management for pgvector."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import Json, execute_values
from pgvector.psycopg2 import register_vector


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://threat:hunt@localhost:5432/threat_hunt"
)


def get_connection():
    """Create a new database connection."""
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn


@contextmanager
def get_cursor():
    """Context manager for database cursor."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_cursor() as cur:
        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Create log_events table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS log_events (
                id SERIAL PRIMARY KEY,
                raw_log JSONB NOT NULL,
                raw_text TEXT NOT NULL,
                iocs JSONB,
                embedding vector(384),
                source_file TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Create index for vector similarity search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS log_events_embedding_idx
            ON log_events
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)

    print("Database initialized.")


def drop_tables():
    """Drop all tables (for development)."""
    with get_cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS log_events CASCADE")
    print("Tables dropped.")
