"""CLI interface for threat hunting."""

from pathlib import Path

import typer

from .db import init_db, drop_tables, get_connection
from .pipeline import ingest_file, ingest_directory
from .store import get_event_count
from .query import expand_query


app = typer.Typer(
    name="hunt",
    help="LLM-powered threat hunting CLI"
)


@app.command()
def ingest(
    path: Path = typer.Argument(
        ...,
        help="Path to parquet file or directory containing parquet files"
    ),
    batch_size: int = typer.Option(
        100,
        "--batch-size", "-b",
        help="Number of records to process per batch"
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Drop and recreate tables before ingesting"
    )
):
    """Ingest security logs into the vector database."""
    if reset:
        typer.confirm("This will delete all existing data. Continue?", abort=True)
        drop_tables()

    init_db()

    if path.is_file():
        ingest_file(path, batch_size)
    elif path.is_dir():
        ingest_directory(path, batch_size)
    else:
        typer.echo(f"Error: {path} does not exist", err=True)
        raise typer.Exit(1)

    count = get_event_count()
    typer.echo(f"\nDatabase now contains {count} events")


@app.command()
def init():
    """Initialize the database schema."""
    init_db()


@app.command()
def reset():
    """Drop all tables and recreate schema."""
    typer.confirm("This will delete all existing data. Continue?", abort=True)
    drop_tables()
    init_db()


@app.command()
def status():
    """Show database status."""
    try:
        count = get_event_count()
        typer.echo(f"Events in database: {count}")
    except Exception as e:
        typer.echo(f"Error connecting to database: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def logs(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries to show"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Show full raw_log JSON"),
):
    """View log entries from the database."""
    from .db import get_cursor
    import json

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, raw_log, raw_text, iocs, source_file, created_at
            FROM log_events
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        rows = cur.fetchall()

    if not rows:
        typer.echo("No log entries found.")
        return

    for row in rows:
        id_, raw_log, raw_text, iocs, source_file, created_at = row
        typer.echo(f"\n{'='*60}")
        typer.echo(f"ID: {id_} | Source: {source_file}")
        typer.echo(f"Time: {created_at}")

        if raw:
            # Show full raw_log JSON
            typer.echo(f"\n{json.dumps(raw_log, indent=2)}")
        else:
            # Show truncated raw_text
            text_preview = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
            typer.echo(f"\n{text_preview}")

            # Show IOCs if present
            if iocs and any(iocs.values()):
                typer.echo(f"\nIOCs: {json.dumps(iocs, indent=2)}")


@app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON for JSONB columns"),
):
    """Execute a SQL query against the database."""
    from .db import get_cursor
    import json

    with get_cursor() as cur:
        try:
            cur.execute(sql)
        except Exception as e:
            typer.echo(f"Query error: {e}", err=True)
            raise typer.Exit(1)

        # Check if query returns results
        if cur.description is None:
            typer.echo("Query executed successfully (no results returned).")
            return

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        if not rows:
            typer.echo("No results.")
            return

        # Display results
        for row in rows:
            typer.echo(f"\n{'='*60}")
            for col, val in zip(columns, row):
                if isinstance(val, dict) and raw:
                    typer.echo(f"{col}:\n{json.dumps(val, indent=2)}")
                elif isinstance(val, dict):
                    # Compact JSON for non-raw mode
                    typer.echo(f"{col}: {json.dumps(val)[:200]}...")
                else:
                    typer.echo(f"{col}: {val}")

        typer.echo(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")


@app.command()
def enrich(
    batch_size: int = typer.Option(500, "--batch-size", "-b", help="Records per batch"),
):
    """Re-enrich existing log entries with updated IOC detection."""
    from .db import get_cursor
    from .enricher import extract_iocs
    from psycopg2.extras import Json

    # Count total
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM log_events")
        total = cur.fetchone()[0]

    if total == 0:
        typer.echo("No log entries to enrich.")
        return

    typer.echo(f"Re-enriching {total} log entries...")

    processed = 0
    offset = 0

    while offset < total:
        with get_cursor() as cur:
            # Fetch batch
            cur.execute(
                "SELECT id, raw_text FROM log_events ORDER BY id LIMIT %s OFFSET %s",
                (batch_size, offset)
            )
            rows = cur.fetchall()

            if not rows:
                break

            # Re-enrich and update
            for id_, raw_text in rows:
                iocs = extract_iocs(raw_text)
                cur.execute(
                    "UPDATE log_events SET iocs = %s WHERE id = %s",
                    (Json(iocs), id_)
                )

            processed += len(rows)
            offset += batch_size
            typer.echo(f"  Progress: {processed}/{total}")

    typer.echo(f"Done. Enriched {processed} entries.")


@app.command()
def expand(
    query: str = typer.Argument(..., help="Natural language threat hunting query"),
    offline: bool = typer.Option(False, "--offline", help="Use offline expansion (no API call)"),
    model: str = typer.Option("claude-sonnet-4-20250514", "--model", "-m", help="Claude model to use"),
):
    """Expand a threat hunting query into concrete examples.

    Step 1 of the query pipeline: Uses Claude to generate specific
    patterns, event IDs, and indicators to search for.
    """
    if offline:
        from .query.expander import expand_query_offline
        result = expand_query_offline(query, verbose=True)
    else:
        try:
            result = expand_query(query, model=model, verbose=True)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    typer.echo(f"\n{'='*60}")
    typer.echo(f"Original: {result.original_query}")
    typer.echo(f"Model: {result.model}")
    typer.echo(f"Tokens: {result.tokens_used}")
    typer.echo(f"\nExpanded query:")
    typer.echo(f"  {result.expanded_query}")


def main():
    app()


if __name__ == "__main__":
    main()
