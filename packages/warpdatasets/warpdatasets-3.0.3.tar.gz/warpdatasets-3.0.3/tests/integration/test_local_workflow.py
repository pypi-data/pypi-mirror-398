"""Integration tests for local-first workflow.

Tests the complete local workflow:
- Workspace root concept
- warpdata register command
- warpdata ls command
- local:// URI resolution
- Directory artifact support
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


@pytest.fixture
def local_workspace(tmp_path):
    """Create a local workspace structure.

    Creates:
    - workspace_root/data/test/sample/images/ (image files)
    - workspace_root/data/test/sample/main.parquet (table)
    """
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    # Create data directory
    data_dir = workspace_root / "data" / "test" / "sample"
    data_dir.mkdir(parents=True)

    # Create images directory
    images_dir = data_dir / "images"
    images_dir.mkdir()

    # Create sample images
    for i in range(3):
        img_path = images_dir / f"image_{i}.png"
        img_path.write_bytes(f"PNG IMAGE DATA {i}".encode())

    # Create parquet table
    table = pa.table({
        "id": [0, 1, 2],
        "image_path": ["image_0.png", "image_1.png", "image_2.png"],
        "label": ["cat", "dog", "bird"],
    })
    pq.write_table(table, data_dir / "main.parquet")

    return workspace_root, data_dir


class TestLocalWorkspaceSettings:
    """Tests for workspace root configuration."""

    def test_settings_has_workspace_root(self):
        """Settings has workspace_root attribute."""
        from warpdatasets.config.settings import Settings

        settings = Settings()
        assert settings.workspace_root is not None
        assert isinstance(settings.workspace_root, Path)

    def test_settings_resolve_local_uri(self, tmp_path):
        """Settings can resolve local:// URIs."""
        from warpdatasets.config.settings import Settings

        settings = Settings(workspace_root=tmp_path)

        # Test local:// URI resolution
        resolved = settings.resolve_local_uri("local://data/test/file.txt")
        assert resolved == tmp_path / "data" / "test" / "file.txt"

        # Test relative path resolution
        resolved = settings.resolve_local_uri("data/test/file.txt")
        assert resolved == tmp_path / "data" / "test" / "file.txt"

    def test_settings_scope_default(self):
        """Settings defaults to local scope."""
        from warpdatasets.config.settings import Settings

        settings = Settings()
        assert settings.scope == "local"


class TestLocalUriValidation:
    """Tests for local:// URI validation."""

    def test_local_uri_allowed_in_local_scope(self):
        """local:// URIs are allowed in local scope."""
        from warpdatasets.manifest.validate import validate_manifest
        from warpdatasets.manifest.model import (
            Manifest, TableDescriptor, ShardInfo,
        )

        manifest = Manifest(
            dataset="test/sample",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="local://data/test/main.parquet")],
                ),
            },
        )

        # Should not raise in local scope
        validate_manifest(manifest, scope="local")

    def test_local_uri_rejected_in_published_scope(self):
        """local:// URIs are rejected in published scope."""
        from warpdatasets.manifest.validate import validate_manifest, ValidationError
        from warpdatasets.manifest.model import (
            Manifest, TableDescriptor, ShardInfo,
        )

        manifest = Manifest(
            dataset="test/sample",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="local://data/test/main.parquet")],
                ),
            },
        )

        # Should raise in published scope
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(manifest, scope="published")

        assert "local://" in str(exc_info.value)


class TestDirectoryArtifact:
    """Tests for directory artifact support."""

    def test_directory_artifact_kind_is_valid(self):
        """directory is a valid artifact kind."""
        from warpdatasets.manifest.validate import KNOWN_ARTIFACT_KINDS

        assert "directory" in KNOWN_ARTIFACT_KINDS

    def test_file_path_ref_type_compatible_with_directory(self):
        """file_path ref_type is compatible with directory artifacts."""
        from warpdatasets.manifest.validate import REF_TYPE_ARTIFACT_COMPATIBILITY

        assert "file_path" in REF_TYPE_ARTIFACT_COMPATIBILITY
        assert "directory" in REF_TYPE_ARTIFACT_COMPATIBILITY["file_path"]

    def test_resolver_reads_from_directory(self, local_workspace):
        """ArtifactResolver can read from directory artifacts."""
        workspace_root, data_dir = local_workspace

        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.config.settings import Settings

        settings = Settings(workspace_root=workspace_root)

        # Create directory artifact descriptor
        artifact = ArtifactDescriptor(
            kind="directory",
            shards=[ShardInfo(uri=f"local://data/test/sample/images")],
        )

        resolver = ArtifactResolver(
            artifacts={"images": artifact},
            settings=settings,
        )

        # Read file from directory
        content = resolver.read_bytes("images", "image_0.png")
        assert content == b"PNG IMAGE DATA 0"

        content = resolver.read_bytes("images", "image_2.png")
        assert content == b"PNG IMAGE DATA 2"

    def test_resolver_prevents_path_traversal(self, local_workspace):
        """Resolver prevents path traversal attacks."""
        workspace_root, data_dir = local_workspace

        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.config.settings import Settings
        from warpdatasets.util.errors import RefNotFoundError

        settings = Settings(workspace_root=workspace_root)

        artifact = ArtifactDescriptor(
            kind="directory",
            shards=[ShardInfo(uri=f"local://data/test/sample/images")],
        )

        resolver = ArtifactResolver(
            artifacts={"images": artifact},
            settings=settings,
        )

        # Attempt path traversal
        with pytest.raises(RefNotFoundError):
            resolver.read_bytes("images", "../main.parquet")

        with pytest.raises(RefNotFoundError):
            resolver.read_bytes("images", "../../sample/main.parquet")


class TestRegisterCommand:
    """Tests for warpdata register command."""

    def test_register_creates_manifest(self, local_workspace):
        """register command creates manifest in workspace."""
        workspace_root, data_dir = local_workspace

        from warpdatasets.cli.commands.register import (
            parse_table_arg,
            build_local_manifest,
            compute_content_hash,
        )

        # Parse table arg
        table_spec = parse_table_arg(f"main={data_dir / 'main.parquet'}")
        assert table_spec.name == "main"
        assert len(table_spec.shard_paths) == 1

        # Build manifest
        manifest = build_local_manifest(
            dataset_id="test/sample",
            tables=[table_spec],
            artifacts=[],
            workspace_root=workspace_root,
        )

        assert manifest["dataset"] == "test/sample"
        assert "main" in manifest["tables"]
        assert manifest["tables"]["main"]["row_count"] == 3

    def test_register_with_directory_artifact(self, local_workspace):
        """register can include directory artifacts."""
        workspace_root, data_dir = local_workspace

        from warpdatasets.cli.commands.register import (
            parse_table_arg,
            parse_artifact_arg,
            build_local_manifest,
        )

        table_spec = parse_table_arg(f"main={data_dir / 'main.parquet'}")
        artifact_spec = parse_artifact_arg(f"images={data_dir / 'images'}:image")

        manifest = build_local_manifest(
            dataset_id="test/sample",
            tables=[table_spec],
            artifacts=[artifact_spec],
            workspace_root=workspace_root,
        )

        assert "images" in manifest["artifacts"]
        assert manifest["artifacts"]["images"]["kind"] == "directory"
        assert len(manifest["bindings"]) == 1
        assert manifest["bindings"][0]["media_type"] == "image"
        assert manifest["bindings"][0]["ref_type"] == "file_path"


class TestLsCommand:
    """Tests for warpdata ls command."""

    def test_discover_local_datasets(self, tmp_path):
        """ls discovers datasets in workspace."""
        from warpdatasets.cli.commands.ls import discover_local_datasets

        workspace_root = tmp_path / "workspace"

        # Create manifest structure
        manifest_dir = workspace_root / "manifests" / "test" / "sample"
        manifest_dir.mkdir(parents=True)

        # Create manifest
        manifest = {
            "dataset": "test/sample",
            "tables": {
                "main": {
                    "format": "parquet",
                    "shards": [],
                    "row_count": 100,
                },
            },
            "artifacts": {},
        }
        version = "abc123def456"
        with open(manifest_dir / f"{version}.json", "w") as f:
            json.dump(manifest, f)

        # Create latest pointer
        with open(manifest_dir / "latest.json", "w") as f:
            json.dump({"version": version}, f)

        # Discover datasets
        datasets = list(discover_local_datasets(workspace_root))

        assert len(datasets) == 1
        ds = datasets[0]
        assert ds.dataset_id == "test/sample"
        assert ds.version == version
        assert ds.is_latest is True
        assert ds.row_count == 100

    def test_discover_multiple_versions(self, tmp_path):
        """ls discovers all versions of a dataset."""
        from warpdatasets.cli.commands.ls import discover_local_datasets

        workspace_root = tmp_path / "workspace"
        manifest_dir = workspace_root / "manifests" / "test" / "sample"
        manifest_dir.mkdir(parents=True)

        # Create multiple versions
        versions = ["v1_hash", "v2_hash", "v3_hash"]
        for i, version in enumerate(versions):
            manifest = {
                "dataset": "test/sample",
                "tables": {"main": {"format": "parquet", "shards": [], "row_count": (i + 1) * 10}},
                "artifacts": {},
            }
            with open(manifest_dir / f"{version}.json", "w") as f:
                json.dump(manifest, f)

        # Set latest
        with open(manifest_dir / "latest.json", "w") as f:
            json.dump({"version": "v3_hash"}, f)

        # Discover all versions
        datasets = list(discover_local_datasets(workspace_root))

        assert len(datasets) == 3
        latest = [ds for ds in datasets if ds.is_latest]
        assert len(latest) == 1
        assert latest[0].version == "v3_hash"


class TestLocalResolverIntegration:
    """Integration tests for local:// URI resolution."""

    def test_resolver_with_local_uri(self, local_workspace):
        """Resolver handles local:// URIs in artifact shards."""
        workspace_root, data_dir = local_workspace

        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.config.settings import Settings

        settings = Settings(workspace_root=workspace_root)

        # Create artifact with local:// URI
        artifact = ArtifactDescriptor(
            kind="directory",
            shards=[ShardInfo(uri="local://data/test/sample/images")],
        )

        resolver = ArtifactResolver(
            artifacts={"images": artifact},
            settings=settings,
        )

        # Should resolve and read
        content = resolver.read_bytes("images", "image_1.png")
        assert content == b"PNG IMAGE DATA 1"

    def test_resolver_without_settings_uses_relative(self, local_workspace):
        """Resolver falls back to relative paths without settings."""
        workspace_root, data_dir = local_workspace
        images_dir = data_dir / "images"

        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo

        # Use absolute path (file://) without settings
        artifact = ArtifactDescriptor(
            kind="directory",
            shards=[ShardInfo(uri=f"file://{images_dir}")],
        )

        resolver = ArtifactResolver(
            artifacts={"images": artifact},
        )

        # Should work with file:// URI
        content = resolver.read_bytes("images", "image_0.png")
        assert content == b"PNG IMAGE DATA 0"
