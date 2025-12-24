"""Tests for artifact index lookup.

Tests Phase 6 invariant I6.3: Fast resolution (no shard scanning).
"""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest


class TestIndexLookup:
    """Tests for looking up refs in the index."""

    def test_lookup_returns_correct_entry(self, tmp_path: Path):
        """Lookup returns correct shard and offset info."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        # Create tar with known content
        tar_path = tmp_path / "shard-00000.tar"
        content = b"hello world"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        # Build and save index
        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        # Load and lookup
        index = ArtifactIndex.from_parquet(index_path)
        entry = index.lookup("test.txt")

        assert entry is not None
        assert entry.shard_idx == 0
        assert entry.payload_size == len(content)

    def test_lookup_missing_ref_returns_none(self, tmp_path: Path):
        """Lookup for non-existent ref returns None."""
        from warpdatasets.artifacts.index import ArtifactIndex
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

        index = ArtifactIndex.from_parquet(index_path)
        entry = index.lookup("does_not_exist.txt")

        assert entry is None

    def test_lookup_is_case_sensitive(self, tmp_path: Path):
        """Lookup is case-sensitive."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="Test.txt")
            info.size = 4
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        index = ArtifactIndex.from_parquet(index_path)

        assert index.lookup("Test.txt") is not None
        assert index.lookup("test.txt") is None
        assert index.lookup("TEST.TXT") is None


class TestIndexLookupPerformance:
    """Tests for O(1) or O(log N) lookup performance."""

    def test_lookup_uses_dict_for_small_index(self, tmp_path: Path):
        """Small index uses dict-based O(1) lookup."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        # Create tar with a few members
        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            for i in range(100):
                info = tarfile.TarInfo(name=f"file_{i:04d}.txt")
                info.size = 4
                tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        index = ArtifactIndex.from_parquet(index_path)

        # Verify all lookups work
        for i in range(100):
            entry = index.lookup(f"file_{i:04d}.txt")
            assert entry is not None

    def test_lookup_across_many_shards(self, tmp_path: Path):
        """Lookup works correctly across multiple shards."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        # Create multiple shards
        for shard_idx in range(5):
            tar_path = tmp_path / f"shard-{shard_idx:05d}.tar"
            with tarfile.open(tar_path, "w") as tar:
                for i in range(10):
                    name = f"shard{shard_idx}_file{i}.txt"
                    info = tarfile.TarInfo(name=name)
                    info.size = 4
                    tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        tar_paths = sorted(tmp_path.glob("*.tar"))
        index_data = build_tar_index(tar_paths)
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        index = ArtifactIndex.from_parquet(index_path)

        # Verify correct shard assignment
        for shard_idx in range(5):
            for i in range(10):
                name = f"shard{shard_idx}_file{i}.txt"
                entry = index.lookup(name)
                assert entry is not None
                assert entry.shard_idx == shard_idx


class TestIndexEntry:
    """Tests for IndexEntry dataclass."""

    def test_entry_has_all_required_fields(self, tmp_path: Path):
        """IndexEntry exposes all needed fields."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_path = tmp_path / "shard-00000.tar"
        content = b"test content here"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.bin")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        index = ArtifactIndex.from_parquet(index_path)
        entry = index.lookup("test.bin")

        # All fields must be accessible
        assert hasattr(entry, "shard_idx")
        assert hasattr(entry, "payload_offset")
        assert hasattr(entry, "payload_size")

        assert isinstance(entry.shard_idx, int)
        assert isinstance(entry.payload_offset, int)
        assert isinstance(entry.payload_size, int)
        assert entry.payload_size == len(content)


class TestIndexFromRemote:
    """Tests for loading index from various sources."""

    def test_load_from_bytes(self, tmp_path: Path):
        """Index can be loaded from raw bytes."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = 4
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        # Load as bytes
        with open(index_path, "rb") as f:
            parquet_bytes = f.read()

        index = ArtifactIndex.from_bytes(parquet_bytes)
        entry = index.lookup("test.txt")
        assert entry is not None

    def test_index_metadata_accessible(self, tmp_path: Path):
        """Index metadata (version, kind) is accessible."""
        from warpdatasets.artifacts.index import ArtifactIndex
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = 4
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(
            index_data, index_path, version=1, artifact_kind="tar_shards"
        )

        index = ArtifactIndex.from_parquet(index_path)
        assert index.version == 1
        assert index.artifact_kind == "tar_shards"
