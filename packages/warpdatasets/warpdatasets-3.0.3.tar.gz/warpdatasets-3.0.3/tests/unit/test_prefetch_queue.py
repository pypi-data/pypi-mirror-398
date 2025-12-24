"""Tests for prefetch queue boundedness.

Tests Phase 4 invariant I4.2: Prefetch is non-blocking by default.
"""

from __future__ import annotations

import pytest


class TestPrefetchQueueBoundedness:
    """Tests for prefetch queue size limits."""

    def test_queue_respects_max_size(self):
        """Queue rejects new items when at max size."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=3)

        # Fill queue
        assert queue.enqueue("key1", "s3://bucket/1")
        assert queue.enqueue("key2", "s3://bucket/2")
        assert queue.enqueue("key3", "s3://bucket/3")

        # Queue is full - should reject
        assert not queue.enqueue("key4", "s3://bucket/4")

        # Queue size is at max
        assert queue.size() == 3

    def test_queue_allows_after_dequeue(self):
        """Queue allows new items after dequeue."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=2)

        queue.enqueue("key1", "s3://bucket/1")
        queue.enqueue("key2", "s3://bucket/2")

        # Full
        assert not queue.enqueue("key3", "s3://bucket/3")

        # Dequeue one
        item = queue.dequeue()
        assert item is not None

        # Now can enqueue
        assert queue.enqueue("key3", "s3://bucket/3")


class TestPrefetchQueueDeduplication:
    """Tests for queue deduplication."""

    def test_duplicates_are_deduped(self):
        """Same key is not queued twice."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        # Enqueue same key multiple times
        assert queue.enqueue("key1", "s3://bucket/1")
        assert not queue.enqueue("key1", "s3://bucket/1")  # Already queued
        assert not queue.enqueue("key1", "s3://bucket/1")  # Still queued

        assert queue.size() == 1

    def test_different_keys_not_deduped(self):
        """Different keys are all queued."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")
        queue.enqueue("key2", "s3://bucket/2")
        queue.enqueue("key3", "s3://bucket/3")

        assert queue.size() == 3

    def test_key_can_be_requeued_after_complete(self):
        """Key can be queued again after completion."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")

        # Process and complete
        item = queue.dequeue()
        queue.mark_complete(item.key)

        # Can requeue now
        assert queue.enqueue("key1", "s3://bucket/1")


class TestPrefetchQueueFailureHandling:
    """Tests for handling failures."""

    def test_failures_are_recorded(self):
        """Failed tasks are recorded but don't poison queue."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")

        item = queue.dequeue()
        queue.mark_failed(item.key, "Connection timeout")

        # Queue should be empty after processing
        assert queue.size() == 0

        # Can check failure count
        stats = queue.stats()
        assert stats.failed >= 1

    def test_failed_key_can_be_retried(self):
        """Failed key can be requeued for retry."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")
        item = queue.dequeue()
        queue.mark_failed(item.key, "Error")

        # Can requeue
        assert queue.enqueue("key1", "s3://bucket/1")
        assert queue.size() == 1


class TestPrefetchQueueOrdering:
    """Tests for queue ordering."""

    def test_fifo_ordering(self):
        """Items are dequeued in FIFO order."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")
        queue.enqueue("key2", "s3://bucket/2")
        queue.enqueue("key3", "s3://bucket/3")

        assert queue.dequeue().key == "key1"
        assert queue.dequeue().key == "key2"
        assert queue.dequeue().key == "key3"

    def test_dequeue_returns_none_when_empty(self):
        """dequeue() returns None when queue is empty."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        assert queue.dequeue() is None


class TestPrefetchQueueStats:
    """Tests for queue statistics."""

    def test_stats_tracks_completed(self):
        """Stats track completed count."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")
        item = queue.dequeue()
        queue.mark_complete(item.key)

        stats = queue.stats()
        assert stats.completed >= 1

    def test_stats_tracks_pending(self):
        """Stats track pending count."""
        from warpdatasets.prefetch.queue import PrefetchQueue

        queue = PrefetchQueue(max_size=10)

        queue.enqueue("key1", "s3://bucket/1")
        queue.enqueue("key2", "s3://bucket/2")

        stats = queue.stats()
        assert stats.pending == 2
