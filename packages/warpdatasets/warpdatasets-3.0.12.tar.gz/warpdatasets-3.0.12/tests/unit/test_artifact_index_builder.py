"""Tests for artifact index builder.

Tests Phase 6 invariant I6.2: Deterministic indexing.
"""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest


class TestIndexBuilderCorrectness:
    """Tests that index builder correctly extracts tar member locations."""

    def test_builds_index_for_all_members(self, tmp_path: Path):
        """Index contains entries for all tar members."""
        from warpdatasets.artifacts.tar.index_builder import build_tar_index

        # Create tar with known members
        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            for name in ["a.jpg", "b.png", "c.txt"]:
                data = f"content of {name}".encode()
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        index = build_tar_index([tar_path])

        # Should have entry for each member
        assert len(index) == 3
        refs = {entry["ref"] for entry in index}
        assert refs == {"a.jpg", "b.png", "c.txt"}

    def test_index_contains_correct_shard_idx(self, tmp_path: Path):
        """Each entry has correct shard index."""
        from warpdatasets.artifacts.tar.index_builder import build_tar_index

        # Create two tar shards
        for shard_idx in range(2):
            tar_path = tmp_path / f"shard-{shard_idx:05d}.tar"
            with tarfile.open(tar_path, "w") as tar:
                name = f"file_{shard_idx}.txt"
                data = b"content"
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        tar_paths = sorted(tmp_path.glob("*.tar"))
        index = build_tar_index(tar_paths)

        # Each entry should have correct shard_idx
        for entry in index:
            if entry["ref"] == "file_0.txt":
                assert entry["shard_idx"] == 0
            elif entry["ref"] == "file_1.txt":
                assert entry["shard_idx"] == 1

    def test_index_contains_correct_offsets(self, tmp_path: Path):
        """Index offsets match actual tar layout."""
        from warpdatasets.artifacts.tar.index_builder import build_tar_index

        # Create tar with known content
        tar_path = tmp_path / "shard-00000.tar"
        content_a = b"hello world"
        content_b = b"another file content"

        with tarfile.open(tar_path, "w") as tar:
            info_a = tarfile.TarInfo(name="a.txt")
            info_a.size = len(content_a)
            tar.addfile(info_a, fileobj=__import__("io").BytesIO(content_a))

            info_b = tarfile.TarInfo(name="b.txt")
            info_b.size = len(content_b)
            tar.addfile(info_b, fileobj=__import__("io").BytesIO(content_b))

        index = build_tar_index([tar_path])

        # Verify we can read correct content using offsets
        with open(tar_path, "rb") as f:
            for entry in index:
                f.seek(entry["payload_offset"])
                data = f.read(entry["payload_size"])
                if entry["ref"] == "a.txt":
                    assert data == content_a
                elif entry["ref"] == "b.txt":
                    assert data == content_b

    def test_index_has_correct_payload_sizes(self, tmp_path: Path):
        """Payload sizes match actual file sizes."""
        from warpdatasets.artifacts.tar.index_builder import build_tar_index

        tar_path = tmp_path / "shard-00000.tar"
        sizes = {"small.bin": 10, "medium.bin": 1000, "large.bin": 10000}

        with tarfile.open(tar_path, "w") as tar:
            for name, size in sizes.items():
                data = b"x" * size
                info = tarfile.TarInfo(name=name)
                info.size = size
                tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        index = build_tar_index([tar_path])

        for entry in index:
            expected_size = sizes[entry["ref"]]
            assert entry["payload_size"] == expected_size


class TestIndexDeterminism:
    """Tests that index building is deterministic."""

    def test_same_tars_produce_same_index(self, tmp_path: Path):
        """Building index twice produces identical results."""
        from warpdatasets.artifacts.tar.index_builder import build_tar_index

        # Create tar
        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            for i in range(5):
                name = f"file_{i}.txt"
                data = f"content {i}".encode()
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        # Build index twice
        index1 = build_tar_index([tar_path])
        index2 = build_tar_index([tar_path])

        # Should be identical
        assert index1 == index2

    def test_shard_order_matters(self, tmp_path: Path):
        """Shard indices are based on input order."""
        from warpdatasets.artifacts.tar.index_builder import build_tar_index

        # Create two shards
        for i in range(2):
            tar_path = tmp_path / f"shard-{i:05d}.tar"
            with tarfile.open(tar_path, "w") as tar:
                info = tarfile.TarInfo(name=f"file_{i}.txt")
                info.size = 4
                tar.addfile(info, fileobj=__import__("io").BytesIO(b"data"))

        paths = sorted(tmp_path.glob("*.tar"))
        index = build_tar_index(paths)

        # Verify shard indices match input order
        entry_map = {e["ref"]: e["shard_idx"] for e in index}
        assert entry_map["file_0.txt"] == 0
        assert entry_map["file_1.txt"] == 1


class TestIndexToParquet:
    """Tests for writing index to Parquet format."""

    def test_write_index_to_parquet(self, tmp_path: Path):
        """Index can be written to Parquet file."""
        import pyarrow.parquet as pq
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        # Create tar
        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = 5
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"hello"))

        index = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index, index_path)

        # Verify parquet file exists and is readable
        assert index_path.exists()
        table = pq.read_table(index_path)
        assert len(table) == 1
        assert "ref" in table.column_names
        assert "shard_idx" in table.column_names
        assert "payload_offset" in table.column_names
        assert "payload_size" in table.column_names

    def test_parquet_index_has_metadata(self, tmp_path: Path):
        """Parquet index includes metadata."""
        import pyarrow.parquet as pq
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = 5
            tar.addfile(info, fileobj=__import__("io").BytesIO(b"hello"))

        index = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index, index_path, version=1, artifact_kind="tar_shards")

        # Read metadata
        pf = pq.ParquetFile(index_path)
        metadata = pf.schema_arrow.metadata
        assert metadata is not None
        assert b"index_version" in metadata
        assert b"artifact_kind" in metadata

    def test_parquet_roundtrip(self, tmp_path: Path):
        """Index survives Parquet roundtrip."""
        import pyarrow.parquet as pq
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
            load_index_parquet,
        )

        # Create tar with multiple members
        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            for name in ["a.jpg", "b.png", "c.txt"]:
                data = f"content of {name}".encode()
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        # Build, write, read
        index = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index, index_path)
        loaded = load_index_parquet(index_path)

        # Should match original
        assert len(loaded) == len(index)
        for orig, load in zip(
            sorted(index, key=lambda x: x["ref"]),
            sorted(loaded, key=lambda x: x["ref"]),
        ):
            assert orig == load
