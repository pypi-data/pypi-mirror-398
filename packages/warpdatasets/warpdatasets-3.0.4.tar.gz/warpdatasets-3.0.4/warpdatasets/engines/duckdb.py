"""DuckDB engine adapter for remote parquet scanning."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import duckdb

from warpdatasets.config.settings import Settings, get_settings
from warpdatasets.util.errors import EngineNotReadyError

if TYPE_CHECKING:
    from warpdatasets.manifest.model import TableDescriptor


# Thread-local storage for DuckDB connections
_thread_local = threading.local()


class DuckDBEngine:
    """DuckDB engine for remote parquet scanning.

    Manages DuckDB connections with proper extension configuration
    for remote access (httpfs, S3).
    """

    def __init__(self, settings: Settings | None = None):
        """Initialize DuckDB engine.

        Args:
            settings: Configuration settings (uses global if not provided)
        """
        self.settings = settings or get_settings()
        self._setup_lock = threading.Lock()

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a thread-local DuckDB connection."""
        if not hasattr(_thread_local, "connection"):
            _thread_local.connection = self._create_connection()
        return _thread_local.connection

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create and configure a new DuckDB connection."""
        conn = duckdb.connect(":memory:")

        # Install and load httpfs extension for HTTP/S3 access
        try:
            conn.execute("INSTALL httpfs;")
            conn.execute("LOAD httpfs;")
        except Exception as e:
            raise EngineNotReadyError(
                f"Failed to load httpfs extension: {e}"
            ) from e

        # Configure S3 if settings provided
        if self.settings.s3_region:
            conn.execute(f"SET s3_region = '{self.settings.s3_region}';")

        if self.settings.s3_endpoint_url:
            conn.execute(f"SET s3_endpoint = '{self.settings.s3_endpoint_url}';")
            # For custom endpoints, often need to disable SSL verification
            conn.execute("SET s3_url_style = 'path';")

        return conn

    def _resolve_uri(self, uri: str) -> str:
        """Resolve a URI, converting local:// to file://.

        Args:
            uri: URI to resolve

        Returns:
            Resolved URI (file:// for local, original for others)
        """
        if uri.startswith("local://"):
            path = self.settings.resolve_local_uri(uri)
            return path.as_uri()
        return uri

    def create_relation(
        self,
        table_descriptor: TableDescriptor,
    ) -> duckdb.DuckDBPyRelation:
        """Create a lazy DuckDB relation for a table.

        Args:
            table_descriptor: Table descriptor with shard URIs

        Returns:
            DuckDB relation (lazy, not materialized)

        Note:
            This is a legacy method that only works with uri-based shards.
            For portable manifests, use create_relation_from_uris with
            pre-resolved URIs.
        """
        uris = [self._resolve_uri(uri) for uri in table_descriptor.uris]
        return self.create_relation_from_uris(uris)

    def create_relation_from_uris(
        self,
        uris: list[str],
    ) -> duckdb.DuckDBPyRelation:
        """Create a lazy DuckDB relation from a list of URIs.

        Args:
            uris: List of resolved URIs (file://, s3://, etc.)

        Returns:
            DuckDB relation (lazy, not materialized)
        """
        conn = self._get_connection()

        if not uris:
            raise ValueError("No URIs provided")

        # Build read_parquet query
        if len(uris) == 1:
            query = f"SELECT * FROM read_parquet('{uris[0]}')"
        else:
            # Multiple shards - use list syntax
            uri_list = ", ".join(f"'{uri}'" for uri in uris)
            query = f"SELECT * FROM read_parquet([{uri_list}])"

        return conn.sql(query)

    def describe_schema(
        self,
        table_descriptor: TableDescriptor,
    ) -> dict[str, str]:
        """Get schema from parquet file(s).

        Args:
            table_descriptor: Table descriptor with shard URIs

        Returns:
            Dictionary mapping column names to types
        """
        # If manifest has schema, use it
        if table_descriptor.schema:
            return table_descriptor.schema

        # Otherwise, read from parquet metadata
        relation = self.create_relation(table_descriptor)
        columns = relation.columns
        types = relation.types

        return dict(zip(columns, [str(t) for t in types]))

    def describe_schema_from_uris(
        self,
        uris: list[str],
    ) -> dict[str, str]:
        """Get schema from parquet file(s) using resolved URIs.

        Args:
            uris: List of resolved URIs (file://, s3://, etc.)

        Returns:
            Dictionary mapping column names to types
        """
        if not uris:
            raise ValueError("No URIs provided")

        relation = self.create_relation_from_uris(uris)
        columns = relation.columns
        types = relation.types

        return dict(zip(columns, [str(t) for t in types]))

    def execute_query(self, query: str) -> duckdb.DuckDBPyRelation:
        """Execute a raw SQL query.

        Args:
            query: SQL query string

        Returns:
            DuckDB relation with results
        """
        conn = self._get_connection()
        return conn.sql(query)

    def close(self) -> None:
        """Close the thread-local connection if it exists."""
        if hasattr(_thread_local, "connection"):
            _thread_local.connection.close()
            del _thread_local.connection


# Default engine instance (lazy loaded)
_default_engine: DuckDBEngine | None = None


def get_engine() -> DuckDBEngine:
    """Get the default DuckDB engine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = DuckDBEngine()
    return _default_engine
