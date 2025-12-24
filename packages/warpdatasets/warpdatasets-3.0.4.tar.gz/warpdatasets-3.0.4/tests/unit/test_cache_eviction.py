"""Tests for cache eviction policy.

Tests Phase 4 invariant I4.4: Cache is bounded and garbage-collectable.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestCacheEviction:
    """Tests for cache size limits and eviction."""

    def test_cache_respects_max_size(self, tmp_path: Path):
        """Cache evicts when exceeding max size."""
        from warpdatasets.cache.blob_cache import BlobCache

        # Small cache limit (1KB)
        cache = BlobCache(cache_dir=tmp_path, max_size_bytes=1024)

        # Add 500 bytes
        tmp1 = tmp_path / "temp1"
        tmp1.write_bytes(b"A" * 500)
        cache.put("a" * 64, tmp1, {"uri": "s3://bucket/1", "size": 500})

        # Add another 500 bytes
        tmp2 = tmp_path / "temp2"
        tmp2.write_bytes(b"B" * 500)
        cache.put("b" * 64, tmp2, {"uri": "s3://bucket/2", "size": 500})

        # Add 500 more - should trigger eviction
        tmp3 = tmp_path / "temp3"
        tmp3.write_bytes(b"C" * 500)
        cache.put("c" * 64, tmp3, {"uri": "s3://bucket/3", "size": 500})

        # Cache should have evicted oldest to stay under limit
        stats = cache.stats()
        assert stats.total_bytes <= 1024

    def test_eviction_removes_oldest_first(self, tmp_path: Path):
        """LRU eviction removes least recently used first."""
        import time

        from warpdatasets.cache.blob_cache import BlobCache

        # max_size=199 means eviction triggers when total=200 exceeds it
        # target=179 (90%), so removing one 50-byte item reaches 150 <= 179
        cache = BlobCache(cache_dir=tmp_path, max_size_bytes=199)

        # Add item A (50 bytes) - oldest
        tmp_a = tmp_path / "temp_a"
        tmp_a.write_bytes(b"A" * 50)
        cache.put("a" * 64, tmp_a, {"uri": "s3://bucket/a", "size": 50})
        time.sleep(0.01)

        # Add item B (50 bytes) - newer
        tmp_b = tmp_path / "temp_b"
        tmp_b.write_bytes(b"B" * 50)
        cache.put("b" * 64, tmp_b, {"uri": "s3://bucket/b", "size": 50})
        time.sleep(0.01)

        # Touch A to make it more recent
        cache.touch("a" * 64)
        time.sleep(0.01)

        # Add item C (100 bytes) - should evict B (oldest untouched)
        tmp_c = tmp_path / "temp_c"
        tmp_c.write_bytes(b"C" * 100)
        cache.put("c" * 64, tmp_c, {"uri": "s3://bucket/c", "size": 100})

        # A and C should exist, B should be evicted
        assert cache.has("a" * 64)
        assert cache.has("c" * 64)
        assert not cache.has("b" * 64)


class TestGarbageCollection:
    """Tests for explicit garbage collection."""

    def test_gc_removes_to_target(self, tmp_path: Path):
        """gc() removes entries to reach target size."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path, max_size_bytes=10000)

        # Fill cache with 1000 bytes
        for i in range(10):
            tmp = tmp_path / f"temp_{i}"
            tmp.write_bytes(b"X" * 100)
            key = f"{i:064d}"
            cache.put(key, tmp, {"uri": f"s3://bucket/{i}", "size": 100})

        # Run GC to reduce to 500 bytes
        removed = cache.gc(target_bytes=500)

        assert removed > 0
        assert cache.stats().total_bytes <= 500

    def test_gc_returns_bytes_freed(self, tmp_path: Path):
        """gc() returns number of bytes freed."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path, max_size_bytes=10000)

        # Add 500 bytes
        for i in range(5):
            tmp = tmp_path / f"temp_{i}"
            tmp.write_bytes(b"X" * 100)
            key = f"{i:064d}"
            cache.put(key, tmp, {"uri": f"s3://bucket/{i}", "size": 100})

        initial_size = cache.stats().total_bytes

        # GC to half
        freed = cache.gc(target_bytes=250)

        final_size = cache.stats().total_bytes
        assert freed == initial_size - final_size

    def test_gc_with_no_entries_returns_zero(self, tmp_path: Path):
        """gc() on empty cache returns 0."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        freed = cache.gc(target_bytes=0)
        assert freed == 0


class TestCacheStats:
    """Tests for cache statistics."""

    def test_stats_shows_total_bytes(self, tmp_path: Path):
        """stats() shows correct total bytes."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        # Add 300 bytes
        for i in range(3):
            tmp = tmp_path / f"temp_{i}"
            tmp.write_bytes(b"X" * 100)
            key = f"{i:064d}"
            cache.put(key, tmp, {"uri": f"s3://bucket/{i}", "size": 100})

        stats = cache.stats()
        assert stats.total_bytes == 300

    def test_stats_shows_entry_count(self, tmp_path: Path):
        """stats() shows correct entry count."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        # Add 3 entries
        for i in range(3):
            tmp = tmp_path / f"temp_{i}"
            tmp.write_bytes(b"X" * 50)
            key = f"{i:064d}"
            cache.put(key, tmp, {"uri": f"s3://bucket/{i}", "size": 50})

        stats = cache.stats()
        assert stats.entry_count == 3

    def test_stats_shows_hit_miss_counts(self, tmp_path: Path):
        """stats() tracks cache hits and misses."""
        from warpdatasets.cache.blob_cache import BlobCache

        cache = BlobCache(cache_dir=tmp_path)

        # Add one entry
        tmp = tmp_path / "temp"
        tmp.write_bytes(b"X" * 100)
        cache.put("a" * 64, tmp, {"uri": "s3://bucket/a", "size": 100})

        # Hit
        cache.get_path("a" * 64)
        # Miss
        cache.get_path("b" * 64)
        cache.get_path("c" * 64)

        stats = cache.stats()
        assert stats.hits >= 1
        assert stats.misses >= 2
