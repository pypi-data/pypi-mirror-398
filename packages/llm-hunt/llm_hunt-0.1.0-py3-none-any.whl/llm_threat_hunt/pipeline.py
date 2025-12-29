"""Ingestion pipeline orchestrator."""

from pathlib import Path

from .loader import load_parquet, iter_records, build_raw_text
from .enricher import extract_iocs
from .embedder import embed_batch
from .store import insert_batch
from .db import init_db


def ingest_file(path: Path, batch_size: int = 100) -> int:
    """Ingest a single parquet file into the database.

    Returns the number of records ingested.
    """
    source_file = path.name
    print(f"\nIngesting: {source_file}")

    # Load data
    df = load_parquet(path)
    total = len(df)
    print(f"  Records: {total}")

    ingested = 0
    batch_records = []
    batch_texts = []

    for record in iter_records(df):
        raw_text = build_raw_text(record)
        iocs = extract_iocs(raw_text)

        batch_records.append((record, raw_text, iocs, source_file))
        batch_texts.append(raw_text)

        # Process batch when full
        if len(batch_records) >= batch_size:
            ingested += _process_batch(batch_records, batch_texts)
            batch_records = []
            batch_texts = []
            print(f"  Progress: {ingested}/{total}")

    # Process remaining records
    if batch_records:
        ingested += _process_batch(batch_records, batch_texts)

    print(f"  Completed: {ingested} records")
    return ingested


def _process_batch(
    records: list[tuple[dict, str, dict, str]],
    texts: list[str]
) -> int:
    """Process a batch: embed and store."""
    # Generate embeddings for batch
    embeddings = embed_batch(texts)

    # Prepare for storage
    batch_data = [
        (raw_log, raw_text, iocs, emb, source_file)
        for (raw_log, raw_text, iocs, source_file), emb
        in zip(records, embeddings)
    ]

    # Store batch
    return insert_batch(batch_data)


def ingest_directory(path: Path, batch_size: int = 100) -> int:
    """Ingest all parquet files in a directory.

    Returns total number of records ingested.
    """
    init_db()

    files = list(path.glob("*.parquet"))
    if not files:
        print(f"No parquet files found in {path}")
        return 0

    print(f"Found {len(files)} parquet files")

    total = 0
    for file_path in files:
        total += ingest_file(file_path, batch_size)

    print(f"\nTotal ingested: {total} records")
    return total
