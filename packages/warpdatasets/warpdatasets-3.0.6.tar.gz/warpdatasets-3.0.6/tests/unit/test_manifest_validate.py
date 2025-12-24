"""Tests for manifest validation.

These tests enforce invariant I1.4: Manifest contains no machine-specific absolute local paths.
"""

import os
import pytest

from warpdatasets.manifest.validate import (
    validate_manifest,
    ValidationError,
    ValidationIssue,
)
from warpdatasets.manifest.model import Manifest, TableDescriptor, ShardInfo


class TestFileUriRejection:
    """Tests for file:// URI rejection in published scope (invariant I1.4).

    Note: Default scope is now 'local' for frictionless local development.
    These tests explicitly use scope='published' to test strict validation.
    """

    def test_reject_file_uris_in_published_scope(self):
        """file:// URIs are rejected in published scope."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///home/user/data/part-0000.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        assert any("file://" in str(issue) for issue in exc_info.value.issues)

    def test_file_uris_allowed_in_local_scope(self):
        """file:// URIs are allowed in local scope (default)."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///home/user/data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise in local scope (default)
        validate_manifest(manifest, scope="local")

    def test_reject_multiple_file_uris_in_published_scope(self):
        """All file:// URIs are reported in published scope, not just the first."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///home/user/data/part-0000.parquet"),
                        ShardInfo(uri="s3://bucket/valid.parquet"),
                        ShardInfo(uri="file:///tmp/another.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        # Should report both file:// URIs
        file_issues = [i for i in exc_info.value.issues if "file://" in str(i)]
        assert len(file_issues) >= 2

    def test_allow_file_uris_when_env_enabled(self, monkeypatch):
        """file:// URIs are allowed when WARPDATASETS_ALLOW_FILE_MANIFESTS=1."""
        monkeypatch.setenv("WARPDATASETS_ALLOW_FILE_MANIFESTS", "1")

        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///home/user/data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise
        validate_manifest(manifest)

    def test_allow_file_uris_with_explicit_flag(self):
        """file:// URIs are allowed when allow_file_uris=True."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///home/user/data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise when explicitly allowed
        validate_manifest(manifest, allow_file_uris=True)


class TestTableValidation:
    """Tests for table structure validation."""

    def test_requires_main_table(self):
        """Manifest must have at least a 'main' table."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "other": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        assert any("main" in str(issue).lower() for issue in exc_info.value.issues)

    def test_requires_parquet_format(self):
        """Tables must have format='parquet'."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="csv",  # Invalid
                    shards=[ShardInfo(uri="s3://bucket/data.csv")],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        assert any("parquet" in str(issue).lower() for issue in exc_info.value.issues)

    def test_reject_unknown_table_format(self):
        """Unknown table formats are rejected."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="unknown_format",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        issues_str = str(exc_info.value.issues)
        assert "format" in issues_str.lower() or "parquet" in issues_str.lower()

    def test_reject_empty_tables(self):
        """Manifest must have at least one table."""
        manifest = Manifest(
            dataset="test/example",
            tables={},
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        assert any("table" in str(issue).lower() for issue in exc_info.value.issues)


class TestUriValidation:
    """Tests for URI scheme validation."""

    def test_accept_s3_uris(self):
        """s3:// URIs are valid."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="s3://my-bucket/datasets/data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise
        validate_manifest(manifest)

    def test_accept_https_uris(self):
        """https:// URIs are valid."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="https://example.com/data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise
        validate_manifest(manifest)

    def test_accept_http_uris(self):
        """http:// URIs are valid (though not recommended)."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="http://example.com/data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise
        validate_manifest(manifest)

    def test_reject_relative_paths_in_published_scope(self):
        """Relative paths without scheme are rejected in published scope."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="data/part-0000.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        assert any("scheme" in str(issue).lower() or "uri" in str(issue).lower()
                   for issue in exc_info.value.issues)

    def test_relative_paths_allowed_in_local_scope(self):
        """Relative paths are allowed in local scope for workspace-relative resolution."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="data/part-0000.parquet"),
                    ],
                )
            },
        )

        # Should not raise in local scope (default)
        validate_manifest(manifest, scope="local")

    def test_reject_absolute_local_paths_in_published_scope(self):
        """Absolute local paths without scheme are rejected in published scope."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="/home/user/data/part-0000.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        # Should be rejected as invalid URI
        assert len(exc_info.value.issues) > 0

    def test_reject_unknown_schemes(self):
        """Unknown URI schemes are rejected."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="ftp://server/data.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        assert any("scheme" in str(issue).lower() or "ftp" in str(issue).lower()
                   for issue in exc_info.value.issues)


class TestDatasetIdValidation:
    """Tests for dataset ID format validation."""

    def test_valid_dataset_id(self):
        """Valid workspace/name format passes."""
        manifest = Manifest(
            dataset="my-workspace/my-dataset",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        # Should not raise
        validate_manifest(manifest)

    def test_dataset_id_with_underscores(self):
        """Underscores are allowed in dataset IDs."""
        manifest = Manifest(
            dataset="my_workspace/my_dataset_v2",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        # Should not raise
        validate_manifest(manifest)

    def test_reject_missing_workspace(self):
        """Dataset ID must have workspace/name format."""
        manifest = Manifest(
            dataset="just-a-name",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        assert any("workspace" in str(issue).lower() or "format" in str(issue).lower()
                   for issue in exc_info.value.issues)

    def test_reject_empty_dataset_id(self):
        """Empty dataset ID is rejected."""
        manifest = Manifest(
            dataset="",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)

        assert len(exc_info.value.issues) > 0


class TestValidationErrorDetails:
    """Tests for validation error reporting."""

    def test_validation_error_contains_all_issues(self):
        """ValidationError lists all found issues."""
        manifest = Manifest(
            dataset="invalid",  # Bad format
            tables={
                "other": TableDescriptor(  # Missing 'main'
                    format="csv",  # Bad format
                    shards=[
                        ShardInfo(uri="file:///bad/path.parquet"),  # Bad scheme in published scope
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        # Should have multiple issues
        assert len(exc_info.value.issues) >= 3

    def test_validation_issue_has_location(self):
        """ValidationIssue includes location information."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///bad/path.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        # At least one issue should have location info
        issue = exc_info.value.issues[0]
        assert hasattr(issue, "location") or hasattr(issue, "path")

    def test_validation_error_message_is_helpful(self):
        """ValidationError has a user-friendly message."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="file:///bad/path.parquet"),
                    ],
                )
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        error_str = str(exc_info.value)
        # Should mention what's wrong
        assert "file://" in error_str or "uri" in error_str.lower()
