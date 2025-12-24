"""Tests for tar shard reader (local tar file).

Tests correctness of tar member extraction without remote access.
"""

from __future__ import annotations

import io
import tarfile
import tempfile
from pathlib import Path

import pytest


def create_test_tar(members: dict[str, bytes]) -> bytes:
    """Create a tar archive in memory with given members.

    Args:
        members: Dict mapping member names to their content bytes.

    Returns:
        The tar archive as bytes.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, content in members.items():
            data = io.BytesIO(content)
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tar.addfile(info, data)
    return buf.getvalue()


class TestTarReaderLocal:
    """Tests for reading members from local tar files."""

    def test_read_known_member(self, tmp_path: Path):
        """Can read a known member by name."""
        from warpdatasets.artifacts.tar.reader import TarReader

        # Create a tar file
        tar_bytes = create_test_tar({
            "images/0.png": b"PNG_DATA_0",
            "images/1.png": b"PNG_DATA_1",
            "images/2.png": b"PNG_DATA_2",
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        # Read a member
        reader = TarReader([f"file://{tar_path}"])
        content = reader.read_member("images/1.png")

        assert content == b"PNG_DATA_1"

    def test_open_known_member(self, tmp_path: Path):
        """Can open a known member as a stream."""
        from warpdatasets.artifacts.tar.reader import TarReader

        tar_bytes = create_test_tar({
            "images/test.jpg": b"JPEG_DATA",
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        reader = TarReader([f"file://{tar_path}"])
        with reader.open_member("images/test.jpg") as f:
            content = f.read()

        assert content == b"JPEG_DATA"

    def test_missing_member_raises_ref_not_found(self, tmp_path: Path):
        """Missing member raises RefNotFoundError."""
        from warpdatasets.artifacts.tar.reader import TarReader
        from warpdatasets.util.errors import RefNotFoundError

        tar_bytes = create_test_tar({
            "images/0.png": b"PNG_DATA",
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        reader = TarReader([f"file://{tar_path}"])

        with pytest.raises(RefNotFoundError) as exc_info:
            reader.read_member("images/nonexistent.png")

        assert "nonexistent.png" in str(exc_info.value)

    def test_read_from_multiple_shards(self, tmp_path: Path):
        """Can read members across multiple tar shards."""
        from warpdatasets.artifacts.tar.reader import TarReader

        # Create two tar shards
        shard0_bytes = create_test_tar({
            "images/0.png": b"SHARD0_IMG0",
            "images/1.png": b"SHARD0_IMG1",
        })
        shard1_bytes = create_test_tar({
            "images/2.png": b"SHARD1_IMG2",
            "images/3.png": b"SHARD1_IMG3",
        })

        shard0_path = tmp_path / "shard-0.tar"
        shard1_path = tmp_path / "shard-1.tar"
        shard0_path.write_bytes(shard0_bytes)
        shard1_path.write_bytes(shard1_bytes)

        reader = TarReader([
            f"file://{shard0_path}",
            f"file://{shard1_path}",
        ])

        # Should find members in both shards
        assert reader.read_member("images/0.png") == b"SHARD0_IMG0"
        assert reader.read_member("images/3.png") == b"SHARD1_IMG3"

    def test_read_member_with_max_bytes(self, tmp_path: Path):
        """read_member with max_bytes truncates output."""
        from warpdatasets.artifacts.tar.reader import TarReader

        tar_bytes = create_test_tar({
            "data/large.bin": b"A" * 1000,
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        reader = TarReader([f"file://{tar_path}"])
        content = reader.read_member("data/large.bin", max_bytes=10)

        assert content == b"A" * 10
        assert len(content) == 10

    def test_empty_tar_raises_on_any_member(self, tmp_path: Path):
        """Empty tar raises RefNotFoundError for any member."""
        from warpdatasets.artifacts.tar.reader import TarReader
        from warpdatasets.util.errors import RefNotFoundError

        # Create empty tar
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w"):
            pass
        tar_path = tmp_path / "empty.tar"
        tar_path.write_bytes(buf.getvalue())

        reader = TarReader([f"file://{tar_path}"])

        with pytest.raises(RefNotFoundError):
            reader.read_member("any/member.txt")

    def test_member_with_special_chars(self, tmp_path: Path):
        """Can read members with special characters in names."""
        from warpdatasets.artifacts.tar.reader import TarReader

        tar_bytes = create_test_tar({
            "images/file with spaces.png": b"SPACE_FILE",
            "images/file-with-dash.png": b"DASH_FILE",
            "images/file_with_underscore.png": b"UNDERSCORE_FILE",
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        reader = TarReader([f"file://{tar_path}"])

        assert reader.read_member("images/file with spaces.png") == b"SPACE_FILE"
        assert reader.read_member("images/file-with-dash.png") == b"DASH_FILE"


class TestTarReaderInfo:
    """Tests for getting member info without reading."""

    def test_member_exists_returns_true(self, tmp_path: Path):
        """member_exists returns True for existing member."""
        from warpdatasets.artifacts.tar.reader import TarReader

        tar_bytes = create_test_tar({
            "images/test.png": b"DATA",
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        reader = TarReader([f"file://{tar_path}"])

        assert reader.member_exists("images/test.png") is True

    def test_member_exists_returns_false(self, tmp_path: Path):
        """member_exists returns False for non-existing member."""
        from warpdatasets.artifacts.tar.reader import TarReader

        tar_bytes = create_test_tar({
            "images/test.png": b"DATA",
        })
        tar_path = tmp_path / "data.tar"
        tar_path.write_bytes(tar_bytes)

        reader = TarReader([f"file://{tar_path}"])

        assert reader.member_exists("images/nonexistent.png") is False
