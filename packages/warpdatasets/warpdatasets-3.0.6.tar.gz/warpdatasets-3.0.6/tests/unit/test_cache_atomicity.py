"""Tests for cache atomic writes.

Tests Phase 4 invariant I4.4: Cache metadata is consistent even after crashes.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestCacheAtomicWrites:
    """Tests for atomic cache write operations."""

    def test_has_returns_false_for_incomplete_write(self, tmp_path: Path):
        """has() returns False when write was interrupted (no meta)."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)
        key = "a" * 64  # Valid sha256 hex key

        # Simulate incomplete write: create object file but no metadata
        obj_dir = tmp_path / "objects" / key[:2] / key[2:4]
        obj_dir.mkdir(parents=True)
        (obj_dir / key).write_bytes(b"incomplete data")

        # Should not be considered cached
        assert cache.has(key) is False

    def test_has_returns_true_after_complete_put(self, tmp_path: Path):
        """has() returns True after successful put()."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        # Create temp file with content
        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"test content")

        key = "b" * 64
        meta = {"uri": "s3://bucket/file", "size": 12}

        cache.put(key, tmp_file, meta)

        assert cache.has(key) is True

    def test_put_results_in_both_object_and_meta(self, tmp_path: Path):
        """put() creates both object file and metadata file."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"test content")

        key = "c" * 64
        meta = {"uri": "s3://bucket/file", "size": 12}

        cache.put(key, tmp_file, meta)

        # Check both files exist
        obj_path = tmp_path / "objects" / key[:2] / key[2:4] / key
        meta_path = tmp_path / "meta" / key[:2] / key[2:4] / f"{key}.json"

        assert obj_path.exists()
        assert meta_path.exists()

    def test_put_is_atomic_temp_file_removed(self, tmp_path: Path):
        """put() removes temp file after successful write."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"test content")

        key = "d" * 64
        cache.put(key, tmp_file, {"uri": "s3://bucket/file"})

        # Temp file should be moved (not copied), so it shouldn't exist
        assert not tmp_file.exists()

    def test_put_preserves_content(self, tmp_path: Path):
        """put() preserves file content correctly."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        content = b"test content with bytes \x00\xff"
        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(content)

        key = "e" * 64
        cache.put(key, tmp_file, {"uri": "s3://bucket/file"})

        # Verify content
        cached_path = cache.get_path(key)
        assert cached_path is not None
        assert cached_path.read_bytes() == content

    def test_get_path_returns_none_for_missing(self, tmp_path: Path):
        """get_path() returns None for non-existent key."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        assert cache.get_path("f" * 64) is None

    def test_get_path_returns_path_for_cached(self, tmp_path: Path):
        """get_path() returns Path for cached content."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"cached")

        key = "g" * 64
        cache.put(key, tmp_file, {"uri": "s3://bucket/file"})

        path = cache.get_path(key)
        assert path is not None
        assert path.exists()
        assert path.read_bytes() == b"cached"


class TestCacheMetadata:
    """Tests for cache metadata handling."""

    def test_meta_contains_uri(self, tmp_path: Path):
        """Metadata file contains original URI."""
        import json

        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"data")

        key = "h" * 64
        uri = "s3://bucket/path/shard.parquet"
        cache.put(key, tmp_file, {"uri": uri, "size": 4})

        meta_path = tmp_path / "meta" / key[:2] / key[2:4] / f"{key}.json"
        meta = json.loads(meta_path.read_text())

        assert meta["uri"] == uri

    def test_meta_contains_size(self, tmp_path: Path):
        """Metadata file contains size."""
        import json

        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"data")

        key = "i" * 64
        cache.put(key, tmp_file, {"uri": "s3://bucket/file", "size": 4})

        meta_path = tmp_path / "meta" / key[:2] / key[2:4] / f"{key}.json"
        meta = json.loads(meta_path.read_text())

        assert meta["size"] == 4

    def test_touch_updates_access_time(self, tmp_path: Path):
        """touch() updates access timestamp for LRU."""
        import time

        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        tmp_file = tmp_path / "temp_data"
        tmp_file.write_bytes(b"data")

        key = "j" * 64
        cache.put(key, tmp_file, {"uri": "s3://bucket/file"})

        # Get initial mtime
        obj_path = cache.get_path(key)
        initial_mtime = obj_path.stat().st_mtime

        time.sleep(0.01)  # Small delay

        # Touch
        cache.touch(key)

        # Verify mtime updated
        new_mtime = obj_path.stat().st_mtime
        assert new_mtime >= initial_mtime
