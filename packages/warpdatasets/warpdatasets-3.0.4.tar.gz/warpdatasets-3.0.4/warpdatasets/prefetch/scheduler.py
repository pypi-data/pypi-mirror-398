"""Prefetch scheduler with background worker threads."""

from __future__ import annotations

import logging
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from warpdatasets.cache.blob_cache import BlobCache, compute_cache_key
from warpdatasets.prefetch.queue import PrefetchItem, PrefetchQueue

logger = logging.getLogger(__name__)


@dataclass
class SchedulerStats:
    """Prefetch scheduler statistics."""

    pending: int = 0
    completed: int = 0
    failed: int = 0
    workers_active: int = 0


class PrefetchScheduler:
    """Background scheduler for prefetching shards.

    Runs worker threads that consume from a queue and download
    shards to the cache.
    """

    def __init__(
        self,
        cache: BlobCache,
        queue: PrefetchQueue,
        download_fn: Callable[[str, Path], dict] | None = None,
        workers: int = 2,
    ):
        """Initialize prefetch scheduler.

        Args:
            cache: BlobCache instance for storing downloaded shards
            queue: PrefetchQueue to consume work from
            download_fn: Function(uri, dest_path) -> metadata dict
                         If None, uses default HTTP download
            workers: Number of worker threads
        """
        self._cache = cache
        self._queue = queue
        self._download_fn = download_fn or self._default_download
        self._num_workers = workers

        self._workers: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._active_workers = 0
        self._active_lock = threading.Lock()

    def _default_download(self, uri: str, dest_path: Path) -> dict:
        """Default download function using urllib/fsspec.

        Args:
            uri: URI to download
            dest_path: Destination path for downloaded content

        Returns:
            Metadata dict with uri, size, etag (if available)
        """
        import urllib.request

        # Simple HTTP download
        if uri.startswith(("http://", "https://")):
            req = urllib.request.Request(uri)
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read()
                etag = response.headers.get("ETag")

            dest_path.write_bytes(content)
            return {
                "uri": uri,
                "size": len(content),
                "etag": etag,
            }

        # For S3/GCS URIs, use fsspec if available
        try:
            import fsspec

            fs, path = fsspec.url_to_fs(uri)
            with fs.open(path, "rb") as f:
                content = f.read()

            dest_path.write_bytes(content)

            # Try to get etag from info
            info = fs.info(path)
            etag = info.get("ETag") or info.get("etag")
            size = info.get("size", len(content))

            return {
                "uri": uri,
                "size": size,
                "etag": etag,
            }
        except ImportError:
            raise RuntimeError(f"fsspec required to download {uri}")

    def start(self) -> None:
        """Start worker threads."""
        if self._workers:
            return  # Already started

        self._stop_event.clear()

        for i in range(self._num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"prefetch-worker-{i}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

        logger.debug(f"Started {self._num_workers} prefetch workers")

    def stop(self, timeout: float = 5.0) -> None:
        """Stop all worker threads.

        Args:
            timeout: Max time to wait for workers to finish
        """
        self._stop_event.set()

        for worker in self._workers:
            worker.join(timeout=timeout / len(self._workers) if self._workers else 1)

        self._workers.clear()
        logger.debug("Stopped prefetch workers")

    def schedule(self, uri: str, key: str | None = None) -> bool:
        """Schedule a URI for prefetch.

        Args:
            uri: URI to prefetch
            key: Optional cache key (computed from URI if not provided)

        Returns:
            True if scheduled, False if already queued or queue full
        """
        if key is None:
            key = compute_cache_key(uri)

        # Skip if already cached
        if self._cache.has(key):
            return False

        return self._queue.enqueue(key, uri)

    def schedule_many(self, uris: list[str]) -> int:
        """Schedule multiple URIs for prefetch.

        Args:
            uris: List of URIs to prefetch

        Returns:
            Number of URIs successfully scheduled
        """
        scheduled = 0
        for uri in uris:
            if self.schedule(uri):
                scheduled += 1
        return scheduled

    def stats(self) -> SchedulerStats:
        """Get scheduler statistics.

        Returns:
            SchedulerStats with current counts
        """
        queue_stats = self._queue.stats()
        with self._active_lock:
            active = self._active_workers

        return SchedulerStats(
            pending=queue_stats.pending,
            completed=queue_stats.completed,
            failed=queue_stats.failed,
            workers_active=active,
        )

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while not self._stop_event.is_set():
            item = self._queue.dequeue()

            if item is None:
                # No work available, sleep briefly
                time.sleep(0.05)
                continue

            with self._active_lock:
                self._active_workers += 1

            try:
                self._process_item(item)
            finally:
                with self._active_lock:
                    self._active_workers -= 1

    def _process_item(self, item: PrefetchItem) -> None:
        """Process a single prefetch item.

        Args:
            item: PrefetchItem to download and cache
        """
        # Skip if already cached (could have been cached while in queue)
        if self._cache.has(item.key):
            self._queue.mark_complete(item.key)
            return

        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = Path(tmp.name)

            meta = self._download_fn(item.uri, tmp_path)

            # Store in cache atomically
            self._cache.put(item.key, tmp_path, meta)
            self._queue.mark_complete(item.key)

            logger.debug(f"Prefetched: {item.uri}")

        except Exception as e:
            logger.warning(f"Prefetch failed for {item.uri}: {e}")
            self._queue.mark_failed(item.key, str(e))

            # Clean up temp file if it exists
            if tmp_path.exists():
                tmp_path.unlink()

    def is_running(self) -> bool:
        """Check if scheduler has active workers.

        Returns:
            True if any worker threads are alive
        """
        return any(w.is_alive() for w in self._workers)

    def wait_idle(self, timeout: float = 10.0) -> bool:
        """Wait until queue is empty and no workers are active.

        Args:
            timeout: Max time to wait in seconds

        Returns:
            True if idle, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            stats = self.stats()
            if stats.pending == 0 and stats.workers_active == 0:
                return True
            time.sleep(0.05)
        return False
