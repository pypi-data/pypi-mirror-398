"""Prefetch planners for determining next shards to fetch."""

from __future__ import annotations

from typing import Callable, Sequence


class TableShardPlanner:
    """Planner for table shard prefetching.

    Determines which shards to prefetch based on current streaming position.
    Respects sharding assignment (only plans shards for this worker).
    """

    def __init__(
        self,
        shards: Sequence[str],
        ahead: int = 2,
        is_cached_fn: Callable[[str], bool] | None = None,
    ):
        """Initialize table shard planner.

        Args:
            shards: List of shard URIs assigned to this worker
            ahead: Number of shards to prefetch ahead
            is_cached_fn: Optional function to check if URI is cached
        """
        self._shards = list(shards)
        self._ahead = ahead
        self._is_cached = is_cached_fn or (lambda uri: False)

    def get_next_shards(self, current_index: int) -> list[str]:
        """Get next shards to prefetch from current position.

        Args:
            current_index: Current shard index being processed

        Returns:
            List of shard URIs to prefetch (up to ahead count)
        """
        result = []
        idx = current_index + 1

        while len(result) < self._ahead and idx < len(self._shards):
            uri = self._shards[idx]
            if not self._is_cached(uri):
                result.append(uri)
            idx += 1

        return result

    def get_all_remaining(self, current_index: int) -> list[str]:
        """Get all remaining shards after current position.

        Useful for aggressive prefetch mode.

        Args:
            current_index: Current shard index being processed

        Returns:
            List of all remaining shard URIs (not cached)
        """
        result = []
        for idx in range(current_index + 1, len(self._shards)):
            uri = self._shards[idx]
            if not self._is_cached(uri):
                result.append(uri)
        return result


class ArtifactShardPlanner:
    """Planner for artifact shard prefetching.

    In Phase 4, artifact prefetch is simpler - typically triggered
    on first ref access or prefetch by shard alignment.
    """

    def __init__(
        self,
        shards: Sequence[str],
        is_cached_fn: Callable[[str], bool] | None = None,
    ):
        """Initialize artifact shard planner.

        Args:
            shards: List of artifact shard URIs
            is_cached_fn: Optional function to check if URI is cached
        """
        self._shards = list(shards)
        self._is_cached = is_cached_fn or (lambda uri: False)

    def get_shards_to_prefetch(self, count: int = 1) -> list[str]:
        """Get first N uncached shards to prefetch.

        Args:
            count: Number of shards to return

        Returns:
            List of shard URIs to prefetch
        """
        result = []
        for uri in self._shards:
            if len(result) >= count:
                break
            if not self._is_cached(uri):
                result.append(uri)
        return result
