"""Bounded prefetch queue with deduplication."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from typing import Set


@dataclass
class PrefetchItem:
    """An item in the prefetch queue."""

    key: str
    uri: str


@dataclass
class QueueStats:
    """Queue statistics."""

    pending: int = 0
    completed: int = 0
    failed: int = 0


class PrefetchQueue:
    """Thread-safe bounded queue with deduplication for prefetch tasks.

    Features:
    - Bounded size to prevent unbounded memory use
    - Deduplication: same key not queued twice
    - FIFO ordering
    - Failure tracking
    """

    def __init__(self, max_size: int = 100):
        """Initialize prefetch queue.

        Args:
            max_size: Maximum number of pending items
        """
        self._max_size = max_size
        self._queue: deque[PrefetchItem] = deque()
        self._pending_keys: Set[str] = set()
        self._in_progress_keys: Set[str] = set()

        self._completed = 0
        self._failed = 0

        self._lock = threading.Lock()

    def enqueue(self, key: str, uri: str) -> bool:
        """Add item to queue if not already present.

        Args:
            key: Unique cache key
            uri: URI to fetch

        Returns:
            True if enqueued, False if queue full or already queued
        """
        with self._lock:
            # Already queued or in progress
            if key in self._pending_keys or key in self._in_progress_keys:
                return False

            # Queue full
            if len(self._queue) >= self._max_size:
                return False

            self._queue.append(PrefetchItem(key=key, uri=uri))
            self._pending_keys.add(key)
            return True

    def dequeue(self) -> PrefetchItem | None:
        """Remove and return next item from queue.

        Returns:
            PrefetchItem or None if empty
        """
        with self._lock:
            if not self._queue:
                return None

            item = self._queue.popleft()
            self._pending_keys.discard(item.key)
            self._in_progress_keys.add(item.key)
            return item

    def mark_complete(self, key: str) -> None:
        """Mark item as successfully completed.

        Args:
            key: Cache key
        """
        with self._lock:
            self._in_progress_keys.discard(key)
            self._completed += 1

    def mark_failed(self, key: str, error: str | None = None) -> None:
        """Mark item as failed.

        Args:
            key: Cache key
            error: Optional error message
        """
        with self._lock:
            self._in_progress_keys.discard(key)
            self._failed += 1

    def size(self) -> int:
        """Get current queue size (pending items only).

        Returns:
            Number of pending items
        """
        with self._lock:
            return len(self._queue)

    def stats(self) -> QueueStats:
        """Get queue statistics.

        Returns:
            QueueStats with counts
        """
        with self._lock:
            return QueueStats(
                pending=len(self._queue),
                completed=self._completed,
                failed=self._failed,
            )

    def clear(self) -> None:
        """Clear all pending items."""
        with self._lock:
            self._queue.clear()
            self._pending_keys.clear()
