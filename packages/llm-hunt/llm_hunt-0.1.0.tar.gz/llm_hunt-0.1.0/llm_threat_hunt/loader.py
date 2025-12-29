"""Load and parse security log files."""

import json
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd


def load_parquet(path: Path) -> pd.DataFrame:
    """Load a parquet file into a DataFrame."""
    return pd.read_parquet(path)


def _convert_numpy(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj) if not np.isnan(obj) else None
    if isinstance(obj, np.bool_):
        return bool(obj)
    if pd.isna(obj):
        return None
    return obj


def iter_records(df: pd.DataFrame) -> Iterator[dict]:
    """Iterate over DataFrame rows as dictionaries."""
    for _, row in df.iterrows():
        yield {k: _convert_numpy(v) for k, v in row.to_dict().items()}


def build_raw_text(record: dict) -> str:
    """Build text representation from log record for embedding.

    Extracts all non-empty string fields and formats them as key-value pairs.
    """
    parts = []
    for key, value in record.items():
        if value is None:
            continue
        # Convert to string and skip empty/whitespace-only values
        str_value = str(value).strip()
        if str_value and str_value.lower() not in ('nan', 'none', 'nat'):
            parts.append(f"{key}: {str_value}")

    return " | ".join(parts)


def load_and_prepare(path: Path) -> Iterator[tuple[dict, str]]:
    """Load parquet and yield (raw_log, raw_text) tuples."""
    df = load_parquet(path)
    for record in iter_records(df):
        raw_text = build_raw_text(record)
        yield record, raw_text
