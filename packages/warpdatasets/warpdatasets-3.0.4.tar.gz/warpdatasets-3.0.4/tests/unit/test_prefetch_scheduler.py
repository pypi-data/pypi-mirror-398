"""Tests for prefetch scheduler.

Tests Phase 4 invariant I4.2: Prefetch never blocks main iteration.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest


class TestSchedulerBasics:
    """Tests for basic scheduler functionality."""

    def test_scheduler_starts_and_stops(self, tmp_path: Path):
        """Scheduler can be started and stopped."""
        from warpdatasets.cache.blob_cache import BlobCache
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue()
        scheduler = PrefetchScheduler(cache, queue, workers=2)

        scheduler.start()
        assert scheduler.is_running()

        scheduler.stop()
        assert not scheduler.is_running()

    def test_scheduler_processes_items(self, tmp_path: Path):
        """Scheduler downloads and caches items from queue."""
        from warpdatasets.cache.blob_cache import BlobCache, compute_cache_key
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue()

        # Track downloads
        downloaded = []

        def mock_download(uri: str, dest: Path) -> dict:
            downloaded.append(uri)
            dest.write_bytes(b"test content")
            return {"uri": uri, "size": 12}

        scheduler = PrefetchScheduler(
            cache, queue, download_fn=mock_download, workers=1
        )
        scheduler.start()

        try:
            # Schedule items
            scheduler.schedule("http://example.com/shard1.parquet")
            scheduler.schedule("http://example.com/shard2.parquet")

            # Wait for processing
            scheduler.wait_idle(timeout=2.0)

            # Items should be downloaded
            assert len(downloaded) == 2

            # Items should be cached
            key1 = compute_cache_key("http://example.com/shard1.parquet")
            key2 = compute_cache_key("http://example.com/shard2.parquet")
            assert cache.has(key1)
            assert cache.has(key2)

        finally:
            scheduler.stop()

    def test_scheduler_skips_cached_items(self, tmp_path: Path):
        """Scheduler skips items already in cache."""
        from warpdatasets.cache.blob_cache import BlobCache, compute_cache_key
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue()

        # Pre-cache an item
        uri = "http://example.com/cached.parquet"
        key = compute_cache_key(uri)
        tmp_file = tmp_path / "temp"
        tmp_file.write_bytes(b"cached")
        cache.put(key, tmp_file, {"uri": uri, "size": 6})

        downloaded = []

        def mock_download(uri: str, dest: Path) -> dict:
            downloaded.append(uri)
            dest.write_bytes(b"test")
            return {"uri": uri, "size": 4}

        scheduler = PrefetchScheduler(
            cache, queue, download_fn=mock_download, workers=1
        )
        scheduler.start()

        try:
            # Try to schedule cached item
            result = scheduler.schedule(uri)
            assert not result  # Should return False

            # Downloaded list should be empty
            assert len(downloaded) == 0

        finally:
            scheduler.stop()


class TestSchedulerNonBlocking:
    """Tests for non-blocking prefetch behavior."""

    def test_schedule_returns_immediately(self, tmp_path: Path):
        """schedule() returns immediately without blocking."""
        from warpdatasets.cache.blob_cache import BlobCache
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue()

        slow_download_started = threading.Event()
        slow_download_continue = threading.Event()

        def slow_download(uri: str, dest: Path) -> dict:
            slow_download_started.set()
            slow_download_continue.wait(timeout=5.0)
            dest.write_bytes(b"test")
            return {"uri": uri, "size": 4}

        scheduler = PrefetchScheduler(
            cache, queue, download_fn=slow_download, workers=1
        )
        scheduler.start()

        try:
            # Schedule should return immediately
            start = time.time()
            scheduler.schedule("http://example.com/slow.parquet")
            elapsed = time.time() - start

            # schedule() should complete in under 100ms
            assert elapsed < 0.1

            # Let the download complete
            slow_download_started.wait(timeout=1.0)
            slow_download_continue.set()

        finally:
            scheduler.stop()

    def test_schedule_many_returns_count(self, tmp_path: Path):
        """schedule_many() returns count of successfully scheduled items."""
        from warpdatasets.cache.blob_cache import BlobCache
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue(max_size=5)  # Small queue

        def mock_download(uri: str, dest: Path) -> dict:
            time.sleep(0.5)  # Slow download to fill queue
            dest.write_bytes(b"test")
            return {"uri": uri, "size": 4}

        scheduler = PrefetchScheduler(
            cache, queue, download_fn=mock_download, workers=1
        )
        # Note: not starting scheduler, so queue won't drain

        uris = [f"http://example.com/shard{i}.parquet" for i in range(10)]
        count = scheduler.schedule_many(uris)

        # Should schedule up to max_size (5)
        assert count == 5


class TestSchedulerStats:
    """Tests for scheduler statistics."""

    def test_stats_tracks_completed(self, tmp_path: Path):
        """Stats track completed downloads."""
        from warpdatasets.cache.blob_cache import BlobCache
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue()

        def mock_download(uri: str, dest: Path) -> dict:
            dest.write_bytes(b"test")
            return {"uri": uri, "size": 4}

        scheduler = PrefetchScheduler(
            cache, queue, download_fn=mock_download, workers=2
        )
        scheduler.start()

        try:
            scheduler.schedule("http://example.com/1.parquet")
            scheduler.schedule("http://example.com/2.parquet")
            scheduler.schedule("http://example.com/3.parquet")

            scheduler.wait_idle(timeout=2.0)

            stats = scheduler.stats()
            assert stats.completed == 3
            assert stats.pending == 0

        finally:
            scheduler.stop()

    def test_stats_tracks_failed(self, tmp_path: Path):
        """Stats track failed downloads."""
        from warpdatasets.cache.blob_cache import BlobCache
        from warpdatasets.prefetch.queue import PrefetchQueue
        from warpdatasets.prefetch.scheduler import PrefetchScheduler

        cache = BlobCache(cache_dir=tmp_path / "cache")
        queue = PrefetchQueue()

        def failing_download(uri: str, dest: Path) -> dict:
            raise RuntimeError("Download failed")

        scheduler = PrefetchScheduler(
            cache, queue, download_fn=failing_download, workers=1
        )
        scheduler.start()

        try:
            scheduler.schedule("http://example.com/fail.parquet")
            scheduler.wait_idle(timeout=2.0)

            stats = scheduler.stats()
            assert stats.failed == 1

        finally:
            scheduler.stop()
