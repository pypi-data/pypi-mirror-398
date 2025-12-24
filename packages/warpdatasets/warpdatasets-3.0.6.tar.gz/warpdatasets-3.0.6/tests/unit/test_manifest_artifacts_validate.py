"""Tests for manifest artifacts and bindings validation.

Tests Phase 3 invariants:
- I3.1: Raw data is represented as artifacts, not paths
- I3.4: Bindings are deterministic and dataset-version scoped
"""

from __future__ import annotations

import pytest

from warpdatasets.manifest.model import (
    ArtifactDescriptor,
    Binding,
    Manifest,
    ShardInfo,
    TableDescriptor,
)
from warpdatasets.manifest.validate import ValidationError, validate_manifest


def make_minimal_manifest(
    artifacts: dict | None = None,
    bindings: list | None = None,
    tables: dict | None = None,
) -> Manifest:
    """Create a minimal valid manifest for testing."""
    if tables is None:
        tables = {
            "main": TableDescriptor(
                format="parquet",
                shards=[ShardInfo(uri="s3://bucket/data/shard-0.parquet")],
                schema={"id": "int64", "image": "string"},
            )
        }
    return Manifest(
        dataset="test/dataset",
        tables=tables,
        artifacts=artifacts or {},
        bindings=bindings or [],
    )


class TestArtifactValidation:
    """Tests for artifact validation."""

    def test_valid_tar_shards_artifact(self):
        """Valid tar_shards artifact passes validation."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[
                        ShardInfo(uri="s3://bucket/artifacts/shard-0.tar"),
                        ShardInfo(uri="s3://bucket/artifacts/shard-1.tar"),
                    ],
                    compression="none",
                )
            }
        )
        # Should not raise
        validate_manifest(manifest)

    def test_artifact_unknown_kind_rejected(self):
        """Unknown artifact kind is rejected."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_data": ArtifactDescriptor(
                    kind="unknown_format",
                    shards=[ShardInfo(uri="s3://bucket/data.tar")],
                )
            }
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)
        assert "unknown_format" in str(exc_info.value)
        assert "kind" in str(exc_info.value).lower()

    def test_artifact_empty_shards_rejected(self):
        """Artifact with no shards is rejected."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[],
                )
            }
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)
        assert "shard" in str(exc_info.value).lower()

    def test_artifact_invalid_uri_scheme_rejected_in_published_scope(self):
        """Artifact with invalid URI scheme is rejected in published scope."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="/local/path/data.tar")],
                )
            }
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")
        assert "scheme" in str(exc_info.value).lower()

    def test_artifact_local_path_allowed_in_local_scope(self):
        """Local paths are allowed in local scope."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="/local/path/data.tar")],
                )
            }
        )
        # Should not raise in local scope (default)
        validate_manifest(manifest, scope="local")

    def test_artifact_http_uri_allowed(self):
        """HTTP URIs are allowed for artifacts."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="https://example.com/data.tar")],
                )
            }
        )
        validate_manifest(manifest)

    def test_artifact_file_uri_rejected_in_published_scope(self):
        """file:// URIs are rejected in published scope."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="file:///local/data.tar")],
                )
            }
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")
        assert "file://" in str(exc_info.value)

    def test_artifact_file_uri_allowed_in_local_scope(self):
        """file:// URIs are allowed in local scope (default)."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="file:///local/data.tar")],
                )
            }
        )
        # Should not raise in local scope
        validate_manifest(manifest, scope="local")

    def test_artifact_file_uri_allowed_with_flag(self):
        """file:// URIs are allowed when flag is set."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="file:///local/data.tar")],
                )
            }
        )
        validate_manifest(manifest, allow_file_uris=True)


class TestBindingValidation:
    """Tests for binding validation."""

    def test_valid_binding(self):
        """Valid binding passes validation."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="s3://bucket/data.tar")],
                )
            },
            bindings=[
                Binding(
                    table="main",
                    column="image",
                    artifact="raw_images",
                    ref_type="tar_member_path",
                    media_type="image",
                )
            ],
        )
        validate_manifest(manifest)

    def test_binding_references_existing_artifact(self):
        """Binding must reference an existing artifact."""
        manifest = make_minimal_manifest(
            artifacts={},
            bindings=[
                Binding(
                    table="main",
                    column="image",
                    artifact="nonexistent",
                    ref_type="tar_member_path",
                    media_type="image",
                )
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)
        assert "nonexistent" in str(exc_info.value)
        assert "artifact" in str(exc_info.value).lower()

    def test_binding_references_existing_table(self):
        """Binding must reference an existing table."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="s3://bucket/data.tar")],
                )
            },
            bindings=[
                Binding(
                    table="nonexistent_table",
                    column="image",
                    artifact="raw_images",
                    ref_type="tar_member_path",
                    media_type="image",
                )
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)
        assert "nonexistent_table" in str(exc_info.value)
        assert "table" in str(exc_info.value).lower()

    def test_binding_ref_type_compatible_with_artifact_kind(self):
        """Binding ref_type must be compatible with artifact kind."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="s3://bucket/data.tar")],
                )
            },
            bindings=[
                Binding(
                    table="main",
                    column="image",
                    artifact="raw_images",
                    ref_type="invalid_ref_type",
                    media_type="image",
                )
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)
        assert "ref_type" in str(exc_info.value).lower()

    def test_reject_unknown_media_type(self):
        """Unknown media_type is rejected."""
        manifest = make_minimal_manifest(
            artifacts={
                "raw_images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="s3://bucket/data.tar")],
                )
            },
            bindings=[
                Binding(
                    table="main",
                    column="image",
                    artifact="raw_images",
                    ref_type="tar_member_path",
                    media_type="unknown_type",
                )
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest)
        assert "media_type" in str(exc_info.value).lower()

    def test_valid_media_types(self):
        """All valid media types are accepted."""
        for media_type in ["image", "audio", "file"]:
            manifest = make_minimal_manifest(
                artifacts={
                    "raw_data": ArtifactDescriptor(
                        kind="tar_shards",
                        shards=[ShardInfo(uri="s3://bucket/data.tar")],
                    )
                },
                bindings=[
                    Binding(
                        table="main",
                        column="image",
                        artifact="raw_data",
                        ref_type="tar_member_path",
                        media_type=media_type,
                    )
                ],
            )
            validate_manifest(manifest)

    def test_multiple_bindings_same_table(self):
        """Multiple bindings to same table are allowed."""
        manifest = Manifest(
            dataset="test/dataset",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/data.parquet")],
                    schema={"id": "int64", "image": "string", "audio": "string"},
                )
            },
            artifacts={
                "images": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="s3://bucket/images.tar")],
                ),
                "audio": ArtifactDescriptor(
                    kind="tar_shards",
                    shards=[ShardInfo(uri="s3://bucket/audio.tar")],
                ),
            },
            bindings=[
                Binding(
                    table="main",
                    column="image",
                    artifact="images",
                    ref_type="tar_member_path",
                    media_type="image",
                ),
                Binding(
                    table="main",
                    column="audio",
                    artifact="audio",
                    ref_type="tar_member_path",
                    media_type="audio",
                ),
            ],
        )
        validate_manifest(manifest)


class TestArtifactDescriptorModel:
    """Tests for ArtifactDescriptor model."""

    def test_compression_field_default_none(self):
        """Compression field defaults to None."""
        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri="s3://bucket/data.tar")],
        )
        assert artifact.compression is None

    def test_compression_field_explicit(self):
        """Compression field can be set explicitly."""
        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri="s3://bucket/data.tar")],
            compression="none",
        )
        assert artifact.compression == "none"

    def test_to_dict_includes_compression(self):
        """to_dict includes compression when set."""
        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri="s3://bucket/data.tar")],
            compression="none",
        )
        d = artifact.to_dict()
        assert d["compression"] == "none"

    def test_uris_property(self):
        """uris property returns list of shard URIs."""
        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[
                ShardInfo(uri="s3://bucket/shard-0.tar"),
                ShardInfo(uri="s3://bucket/shard-1.tar"),
            ],
        )
        assert artifact.uris == [
            "s3://bucket/shard-0.tar",
            "s3://bucket/shard-1.tar",
        ]


class TestBindingModel:
    """Tests for Binding model."""

    def test_media_type_field(self):
        """Binding has media_type field."""
        binding = Binding(
            table="main",
            column="image",
            artifact="raw_images",
            ref_type="tar_member_path",
            media_type="image",
        )
        assert binding.media_type == "image"

    def test_to_dict_includes_media_type(self):
        """to_dict includes media_type."""
        binding = Binding(
            table="main",
            column="image",
            artifact="raw_images",
            ref_type="tar_member_path",
            media_type="image",
        )
        d = binding.to_dict()
        assert d["media_type"] == "image"

    def test_from_dict_parses_media_type(self):
        """from_dict parses media_type correctly."""
        data = {
            "dataset": "test/dataset",
            "tables": {
                "main": {
                    "format": "parquet",
                    "shards": [{"uri": "s3://bucket/data.parquet"}],
                }
            },
            "bindings": [
                {
                    "table": "main",
                    "column": "image",
                    "artifact": "raw_images",
                    "ref_type": "tar_member_path",
                    "media_type": "image",
                }
            ],
            "artifacts": {
                "raw_images": {
                    "kind": "tar_shards",
                    "shards": [{"uri": "s3://bucket/images.tar"}],
                }
            },
        }
        manifest = Manifest.from_dict(data)
        assert manifest.bindings[0].media_type == "image"
