"""Batching and streaming utilities for DuckDB.

Provides helpers for building queries and streaming Arrow RecordBatches
from remote parquet files via DuckDB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Sequence

if TYPE_CHECKING:
    import duckdb
    import pyarrow as pa


def quote_identifier(name: str) -> str:
    """Quote a SQL identifier (column name, table name).

    Handles:
    - Reserved words
    - Names with spaces
    - Names with special characters
    - Names containing quotes (escaped by doubling)

    Args:
        name: The identifier to quote

    Returns:
        Quoted identifier safe for SQL
    """
    # Escape any existing double quotes by doubling them
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def build_batch_query(
    uris: Sequence[str],
    columns: Sequence[str] | None,
    limit: int | None,
) -> str:
    """Build a DuckDB query for streaming batches.

    Args:
        uris: Parquet file URIs to read
        columns: Column names to select (None for all)
        limit: Maximum rows to return (None for unlimited)

    Returns:
        SQL query string

    Raises:
        ValueError: If uris is empty
    """
    if not uris:
        raise ValueError("No shard URIs provided. Cannot build query for empty shard list.")

    # Build SELECT clause
    if columns:
        select_clause = ", ".join(quote_identifier(col) for col in columns)
    else:
        select_clause = "*"

    # Build FROM clause
    if len(uris) == 1:
        from_clause = f"read_parquet('{uris[0]}')"
    else:
        uri_list = ", ".join(f"'{uri}'" for uri in uris)
        from_clause = f"read_parquet([{uri_list}])"

    # Build query
    query = f"SELECT {select_clause} FROM {from_clause}"

    if limit is not None:
        query = f"{query} LIMIT {limit}"

    return query


def stream_batches(
    conn: "duckdb.DuckDBPyConnection",
    query: str,
    batch_size: int,
    as_format: str = "arrow",
) -> Iterator["pa.RecordBatch"] | Iterator[dict[str, list]]:
    """Stream batches from a DuckDB query.

    Args:
        conn: DuckDB connection
        query: SQL query to execute
        batch_size: Rows per batch
        as_format: Output format - "arrow" or "dict"

    Yields:
        Arrow RecordBatch or dict-of-lists depending on as_format
    """
    import pyarrow as pa

    # Execute query and get record batch reader
    result = conn.execute(query)

    # Get the record batch reader
    reader = result.fetch_record_batch(batch_size)

    # Iterate over batches from the reader
    for batch in reader:
        if batch.num_rows == 0:
            continue

        if as_format == "dict":
            yield batch.to_pydict()
        else:
            yield batch
