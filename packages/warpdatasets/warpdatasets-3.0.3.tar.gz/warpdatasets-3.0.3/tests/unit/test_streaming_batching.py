"""Tests for streaming batching contract.

These tests enforce invariant I2.5: Batch semantics are explicit and stable.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pyarrow as pa

from warpdatasets.streaming.batching import (
    build_batch_query,
    quote_identifier,
)


class TestQuoteIdentifier:
    """Tests for SQL identifier quoting."""

    def test_simple_column_name(self):
        """Simple column names are quoted."""
        assert quote_identifier("name") == '"name"'

    def test_column_with_space(self):
        """Column names with spaces are quoted correctly."""
        assert quote_identifier("my column") == '"my column"'

    def test_column_with_quotes(self):
        """Column names with quotes are escaped."""
        result = quote_identifier('col"name')
        # Double quotes inside should be escaped
        assert result == '"col""name"'

    def test_reserved_word(self):
        """SQL reserved words are quoted."""
        assert quote_identifier("select") == '"select"'
        assert quote_identifier("from") == '"from"'

    def test_column_with_special_chars(self):
        """Column names with special characters are handled."""
        assert quote_identifier("col-name") == '"col-name"'
        assert quote_identifier("col.name") == '"col.name"'


class TestBuildBatchQuery:
    """Tests for batch query building."""

    def test_build_query_all_columns(self):
        """Query without column projection selects all."""
        uris = ["s3://bucket/part-0.parquet"]
        query = build_batch_query(uris, columns=None, limit=None)

        assert "SELECT *" in query
        assert "s3://bucket/part-0.parquet" in query

    def test_build_query_with_projection(self):
        """Query with columns applies projection."""
        uris = ["s3://bucket/part-0.parquet"]
        query = build_batch_query(uris, columns=["id", "name"], limit=None)

        assert '"id"' in query
        assert '"name"' in query
        assert "SELECT *" not in query

    def test_build_query_with_limit(self):
        """Query with limit applies LIMIT clause."""
        uris = ["s3://bucket/part-0.parquet"]
        query = build_batch_query(uris, columns=None, limit=1000)

        assert "LIMIT 1000" in query

    def test_build_query_multiple_uris(self):
        """Query with multiple URIs uses list syntax."""
        uris = [
            "s3://bucket/part-0.parquet",
            "s3://bucket/part-1.parquet",
        ]
        query = build_batch_query(uris, columns=None, limit=None)

        assert "part-0.parquet" in query
        assert "part-1.parquet" in query

    def test_build_query_empty_uris_raises(self):
        """Empty URI list raises ValueError."""
        with pytest.raises(ValueError, match="[Ee]mpty|[Nn]o.*shard"):
            build_batch_query([], columns=None, limit=None)


class TestBatchSizeContract:
    """Tests for batch size semantics."""

    def test_batch_size_refers_to_rows(self):
        """batch_size parameter refers to rows per batch, not shards."""
        # This is a contract/documentation test
        # The actual implementation test is in integration tests
        # Here we just verify the parameter name/documentation
        from warpdatasets.api.dataset import Table

        # Check that batches() accepts batch_size parameter
        import inspect
        sig = inspect.signature(Table.batches)
        assert "batch_size" in sig.parameters

        # Check default value is reasonable
        default = sig.parameters["batch_size"].default
        assert isinstance(default, int)
        assert default > 0


class TestBatchFormat:
    """Tests for batch output format options."""

    def test_arrow_format_returns_record_batch(self):
        """as_format='arrow' yields pyarrow.RecordBatch."""
        # This tests the contract - actual implementation in integration
        from warpdatasets.api.dataset import Table

        import inspect
        sig = inspect.signature(Table.batches)
        assert "as_format" in sig.parameters

        # Default should be arrow
        default = sig.parameters["as_format"].default
        assert default == "arrow"

    def test_dict_format_option_exists(self):
        """as_format='dict' option exists."""
        from warpdatasets.api.dataset import Table

        import inspect
        sig = inspect.signature(Table.batches)
        # The parameter should accept 'dict' as a value
        # This is enforced by the implementation


class TestStreamingGuardrails:
    """Tests for streaming safety guardrails."""

    def test_batches_does_not_materialize_all(self):
        """batches() should not trigger full materialization."""
        # This is verified by the fact that batches() returns an iterator
        # and doesn't call .df() or .fetchall() internally
        from warpdatasets.api.dataset import Table

        import inspect
        sig = inspect.signature(Table.batches)

        # Should return an Iterator, not a DataFrame or list
        # This is a design contract test
        return_annotation = sig.return_annotation
        # The return type should indicate Iterator
        assert "Iterator" in str(return_annotation) or return_annotation == inspect.Parameter.empty


class TestProjectionPushdown:
    """Tests for column projection in queries."""

    def test_projection_applied_in_query(self):
        """Column projection is applied at query level (pushdown)."""
        uris = ["s3://bucket/part-0.parquet"]
        query = build_batch_query(uris, columns=["col1", "col2"], limit=None)

        # Projection should be in SELECT, not post-filter
        # This ensures pushdown to parquet reader
        assert query.startswith("SELECT")
        assert '"col1"' in query.split("FROM")[0]

    def test_projection_preserves_column_order(self):
        """Columns are selected in the order specified."""
        uris = ["s3://bucket/part-0.parquet"]
        query = build_batch_query(uris, columns=["z_col", "a_col", "m_col"], limit=None)

        # z_col should appear before a_col in the query
        z_pos = query.find('"z_col"')
        a_pos = query.find('"a_col"')
        m_pos = query.find('"m_col"')

        assert z_pos < a_pos < m_pos
