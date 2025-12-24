"""Tests for safety guardrails.

These tests enforce invariant I1.5: Safety guardrails for huge data.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from warpdatasets.util.errors import LargeDataError
from warpdatasets.api.dataset import Table
from warpdatasets.config.settings import Settings
from warpdatasets.manifest.model import Manifest, TableDescriptor, ShardInfo


class TestToPandasGuardrail:
    """Tests for to_pandas() large data protection."""

    def test_to_pandas_requires_limit_when_large(self):
        """to_pandas() raises LargeDataError for large datasets without limit."""
        # Create a table with large row count
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=10_000_000,  # 10 million rows
                )
            },
        )

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=Mock(),
        )

        with pytest.raises(LargeDataError) as exc_info:
            table.to_pandas()

        error = exc_info.value
        assert "10" in str(error) or "million" in str(error).lower()
        assert "limit" in str(error).lower()

    def test_to_pandas_allows_limit(self):
        """to_pandas(limit=N) works for large datasets."""
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=10_000_000,
                )
            },
        )

        mock_engine = Mock()
        mock_relation = MagicMock()
        mock_relation.limit.return_value.df.return_value = Mock()  # pandas df
        mock_engine.create_relation.return_value = mock_relation

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=mock_engine,
        )

        # Should not raise with limit
        result = table.to_pandas(limit=1000)

        mock_relation.limit.assert_called_with(1000)

    def test_to_pandas_allow_large_override(self):
        """to_pandas(allow_large=True) bypasses the guardrail."""
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=10_000_000,
                )
            },
        )

        mock_engine = Mock()
        mock_relation = MagicMock()
        mock_relation.df.return_value = Mock()
        mock_engine.create_relation.return_value = mock_relation

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=mock_engine,
        )

        # Should not raise with allow_large=True
        result = table.to_pandas(allow_large=True)

        mock_relation.df.assert_called_once()

    def test_to_pandas_small_dataset_no_limit_required(self):
        """to_pandas() works without limit for small datasets."""
        manifest = Manifest(
            dataset="test/small",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=1000,  # Small dataset
                )
            },
        )

        mock_engine = Mock()
        mock_relation = MagicMock()
        mock_relation.df.return_value = Mock()
        mock_engine.create_relation.return_value = mock_relation

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=mock_engine,
        )

        # Should not raise for small datasets
        result = table.to_pandas()

        mock_relation.df.assert_called_once()

    def test_to_pandas_unknown_size_is_conservative(self):
        """to_pandas() is conservative when row_count is unknown."""
        manifest = Manifest(
            dataset="test/unknown",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        # Many shards suggests large dataset
                        ShardInfo(uri=f"s3://bucket/part-{i:04d}.parquet")
                        for i in range(100)
                    ],
                    row_count=None,  # Unknown
                )
            },
        )

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=Mock(),
        )

        # Should raise for unknown size with many shards
        with pytest.raises(LargeDataError):
            table.to_pandas()


class TestLargeDataErrorMessages:
    """Tests for LargeDataError message quality."""

    def test_error_message_includes_row_count(self):
        """Error message includes the actual row count."""
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=50_000_000,
                )
            },
        )

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=Mock(),
        )

        with pytest.raises(LargeDataError) as exc_info:
            table.to_pandas()

        error_msg = str(exc_info.value)
        assert "50" in error_msg  # Contains row count

    def test_error_message_includes_remediation(self):
        """Error message includes how to fix the issue."""
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=10_000_000,
                )
            },
        )

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=Mock(),
        )

        with pytest.raises(LargeDataError) as exc_info:
            table.to_pandas()

        error_msg = str(exc_info.value)
        # Should mention the fix options
        assert "limit" in error_msg.lower() or "allow_large" in error_msg.lower()


class TestHeadGuardrail:
    """Tests for head() method guardrails."""

    def test_head_has_default_limit(self):
        """head() has a sensible default limit."""
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=10_000_000,
                )
            },
        )

        mock_engine = Mock()
        mock_relation = MagicMock()
        mock_engine.create_relation.return_value = mock_relation

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=mock_engine,
        )

        table.head()  # No argument

        # Should apply a limit
        mock_relation.limit.assert_called()
        limit_arg = mock_relation.limit.call_args[0][0]
        assert limit_arg <= 100  # Reasonable default

    def test_head_respects_explicit_limit(self):
        """head(n) uses the specified limit."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        mock_engine = Mock()
        mock_relation = MagicMock()
        mock_engine.create_relation.return_value = mock_relation

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=mock_engine,
        )

        table.head(n=42)

        mock_relation.limit.assert_called_with(42)


class TestDuckDBRelationGuardrail:
    """Tests for duckdb() method - no automatic materialization."""

    def test_duckdb_returns_lazy_relation(self):
        """duckdb() returns a lazy relation, not materialized data."""
        manifest = Manifest(
            dataset="test/large",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    row_count=10_000_000,
                )
            },
        )

        mock_engine = Mock()
        mock_relation = MagicMock()
        mock_engine.create_relation.return_value = mock_relation

        table = Table(
            name="main",
            descriptor=manifest.tables["main"],
            manifest=manifest,
            settings=Settings(),
            engine=mock_engine,
        )

        result = table.duckdb()

        # Should return the relation without materializing
        assert result == mock_relation
        # df() should NOT have been called
        mock_relation.df.assert_not_called()
        mock_relation.fetchall.assert_not_called()
