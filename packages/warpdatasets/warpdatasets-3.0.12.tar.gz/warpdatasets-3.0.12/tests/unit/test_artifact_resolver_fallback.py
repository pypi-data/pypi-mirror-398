"""Tests for resolver fallback behavior when index is missing.

Tests Phase 6 invariant I6.1: Index is optional and backward compatible.
"""

from __future__ import annotations

import tarfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestResolverFallbackToScan:
    """Tests that resolver falls back to scanning when no index."""

    def test_works_without_index(self, tmp_path: Path):
        """Resolver works correctly without index (Phase 3 behavior)."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo

        # Create tar without index
        tar_path = tmp_path / "shard-00000.tar"
        content = b"file content"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        # Artifact without index
        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"file://{tar_path}")],
            index=None,  # No index
        )

        resolver = ArtifactResolver(
            artifacts={"data": artifact},
            cache_context=None,
        )

        # Should still work via scanning
        result = resolver.read_bytes("data", "test.txt")
        assert result == content

    def test_falls_back_when_ref_not_in_index(self, tmp_path: Path):
        """Resolver falls back to scanning if ref not found in index."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        # Create tar with one file
        tar_path = tmp_path / "shard-00000.tar"
        content = b"original content"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="indexed.txt")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        # Build index for just this file
        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        # Now add another file to the tar (simulating stale index)
        new_content = b"new file not in index"
        with tarfile.open(tar_path, "a") as tar:
            info = tarfile.TarInfo(name="not_indexed.txt")
            info.size = len(new_content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(new_content))

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"file://{tar_path}")],
            index=ShardInfo(uri=f"file://{index_path}"),
        )

        resolver = ArtifactResolver(
            artifacts={"data": artifact},
            cache_context=None,
        )

        # Indexed file should work
        result = resolver.read_bytes("data", "indexed.txt")
        assert result == content

        # Non-indexed file should also work via fallback
        result = resolver.read_bytes("data", "not_indexed.txt")
        assert result == new_content

    def test_uses_tar_reader_when_no_index(self, tmp_path: Path):
        """Confirms TarReader is used when no index available."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo

        tar_path = tmp_path / "shard-00000.tar"
        content = b"content"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="file.txt")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"file://{tar_path}")],
            index=None,
        )

        resolver = ArtifactResolver(
            artifacts={"data": artifact},
            cache_context=None,
        )

        # TarReader should be created and used
        result = resolver.read_bytes("data", "file.txt")
        assert result == content
        # The resolver should have created a TarReader
        assert "data" in resolver._reader_cache


class TestBackwardCompatibility:
    """Tests for backward compatibility with Phase 3 manifests."""

    def test_phase3_manifest_still_works(self, tmp_path: Path):
        """Manifests from Phase 3 (no index) still work."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo

        # Create multiple shards (Phase 3 style)
        contents = {}
        shard_uris = []
        for shard_idx in range(3):
            tar_path = tmp_path / f"shard-{shard_idx:05d}.tar"
            shard_uris.append(f"file://{tar_path}")
            with tarfile.open(tar_path, "w") as tar:
                for i in range(3):
                    name = f"s{shard_idx}_f{i}.txt"
                    data = f"content {shard_idx}-{i}".encode()
                    contents[name] = data
                    info = tarfile.TarInfo(name=name)
                    info.size = len(data)
                    tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        # Phase 3 descriptor - no index field
        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=uri) for uri in shard_uris],
            # index is None by default
        )

        resolver = ArtifactResolver(
            artifacts={"images": artifact},
            cache_context=None,
        )

        # All files should be accessible
        for name, expected in contents.items():
            result = resolver.read_bytes("images", name)
            assert result == expected

    def test_open_works_without_index(self, tmp_path: Path):
        """open() method works without index."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo

        tar_path = tmp_path / "shard-00000.tar"
        content = b"binary content"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="data.bin")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"file://{tar_path}")],
        )

        resolver = ArtifactResolver(
            artifacts={"data": artifact},
            cache_context=None,
        )

        with resolver.open("data", "data.bin") as f:
            result = f.read()
            assert result == content


class TestMissingRefError:
    """Tests for error handling when ref not found."""

    def test_raises_ref_not_found_without_index(self, tmp_path: Path):
        """Raises RefNotFoundError when ref doesn't exist (no index)."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.util.errors import RefNotFoundError

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="exists.txt")
            info.size = 4
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"file://{tar_path}")],
        )

        resolver = ArtifactResolver(
            artifacts={"data": artifact},
            cache_context=None,
        )

        with pytest.raises(RefNotFoundError) as exc_info:
            resolver.read_bytes("data", "missing.txt")

        assert exc_info.value.ref_value == "missing.txt"

    def test_raises_ref_not_found_with_index(self, tmp_path: Path):
        """Raises RefNotFoundError when ref doesn't exist (with index)."""
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.util.errors import RefNotFoundError
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="exists.txt")
            info.size = 4
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"file://{tar_path}")],
            index=ShardInfo(uri=f"file://{index_path}"),
        )

        resolver = ArtifactResolver(
            artifacts={"data": artifact},
            cache_context=None,
        )

        with pytest.raises(RefNotFoundError) as exc_info:
            resolver.read_bytes("data", "missing.txt")

        assert exc_info.value.ref_value == "missing.txt"
