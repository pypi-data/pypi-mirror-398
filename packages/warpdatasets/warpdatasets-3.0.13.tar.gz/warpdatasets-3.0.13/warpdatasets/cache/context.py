"""Cache context for coordinating cache and prefetch."""

from __future__ import annotations

import atexit
import logging
from pathlib import Path
from typing import Callable, Sequence

from warpdatasets.cache.blob_cache import BlobCache, compute_cache_key
from warpdatasets.prefetch.queue import PrefetchQueue
from warpdatasets.prefetch.planners import TableShardPlanner
from warpdatasets.prefetch.scheduler import PrefetchScheduler

logger = logging.getLogger(__name__)


class CacheContext:
    """Context for cache and prefetch coordination.

    Manages the blob cache and prefetch scheduler for a dataset.
    Used to resolve URIs (cache path vs remote) and trigger prefetch.
    """

    def __init__(
        self,
        cache_dir: Path,
        max_size_bytes: int | None = None,
        prefetch_mode: str = "off",
        prefetch_workers: int = 2,
        prefetch_ahead: int = 2,
        download_fn: Callable[[str, Path], dict] | None = None,
    ):
        """Initialize cache context.

        Args:
            cache_dir: Directory for cache storage
            max_size_bytes: Maximum cache size (None for unlimited)
            prefetch_mode: "off", "auto", or "aggressive"
            prefetch_workers: Number of prefetch worker threads
            prefetch_ahead: Shards to prefetch ahead
            download_fn: Custom download function (for testing)
        """
        self._cache = BlobCache(
            cache_dir=cache_dir / "blobs",
            max_size_bytes=max_size_bytes,
        )
        self._prefetch_mode = prefetch_mode
        self._prefetch_ahead = prefetch_ahead

        # Prefetch components (created lazily if needed)
        self._queue: PrefetchQueue | None = None
        self._scheduler: PrefetchScheduler | None = None
        self._download_fn = download_fn

        if prefetch_mode != "off":
            self._queue = PrefetchQueue(max_size=100)
            self._scheduler = PrefetchScheduler(
                cache=self._cache,
                queue=self._queue,
                download_fn=download_fn,
                workers=prefetch_workers,
            )
            self._scheduler.start()
            # Register shutdown
            atexit.register(self._shutdown)

    @property
    def cache(self) -> BlobCache:
        """Get the blob cache."""
        return self._cache

    @property
    def prefetch_enabled(self) -> bool:
        """Check if prefetch is enabled."""
        return self._prefetch_mode != "off"

    def resolve_uri(self, uri: str) -> str:
        """Resolve URI to cached path or return original.

        Args:
            uri: Remote URI

        Returns:
            Local cache path if cached, otherwise original URI
        """
        key = compute_cache_key(uri)
        path = self._cache.get_path(key)

        if path is not None:
            # Return file:// URI for cached content
            return path.as_uri()

        return uri

    def resolve_uris(self, uris: Sequence[str]) -> list[str]:
        """Resolve multiple URIs.

        Args:
            uris: List of remote URIs

        Returns:
            List of resolved URIs (cached or remote)
        """
        return [self.resolve_uri(uri) for uri in uris]

    def is_cached(self, uri: str) -> bool:
        """Check if URI is cached.

        Args:
            uri: Remote URI

        Returns:
            True if cached
        """
        key = compute_cache_key(uri)
        return self._cache.has(key)

    def create_planner(
        self,
        shards: Sequence[str],
    ) -> TableShardPlanner:
        """Create a prefetch planner for shards.

        Args:
            shards: Shard URIs for this worker

        Returns:
            TableShardPlanner configured with cache awareness
        """
        return TableShardPlanner(
            shards=shards,
            ahead=self._prefetch_ahead,
            is_cached_fn=self.is_cached,
        )

    def trigger_prefetch(
        self,
        shards: Sequence[str],
        current_index: int,
    ) -> int:
        """Trigger prefetch for upcoming shards.

        Args:
            shards: All shard URIs for this worker
            current_index: Current shard being processed

        Returns:
            Number of shards scheduled for prefetch
        """
        if not self.prefetch_enabled or self._scheduler is None:
            return 0

        planner = TableShardPlanner(
            shards=shards,
            ahead=self._prefetch_ahead,
            is_cached_fn=self.is_cached,
        )

        if self._prefetch_mode == "aggressive":
            # Prefetch all remaining shards
            next_shards = planner.get_all_remaining(current_index)
        else:
            # Prefetch next N shards
            next_shards = planner.get_next_shards(current_index)

        return self._scheduler.schedule_many(next_shards)

    def warm(self, uris: Sequence[str]) -> int:
        """Warm cache by prefetching URIs.

        Blocks until all URIs are cached or failed.

        Args:
            uris: URIs to warm

        Returns:
            Number of URIs successfully cached
        """
        if self._scheduler is None:
            # Create temporary scheduler for warming
            queue = PrefetchQueue(max_size=len(uris) + 10)
            scheduler = PrefetchScheduler(
                cache=self._cache,
                queue=queue,
                download_fn=self._download_fn,
                workers=4,  # More workers for warming
            )
            scheduler.start()
            try:
                scheduled = scheduler.schedule_many(list(uris))
                scheduler.wait_idle(timeout=600)  # 10 minute timeout
                return scheduler.stats().completed
            finally:
                scheduler.stop()
        else:
            initial = self._scheduler.stats().completed
            self._scheduler.schedule_many(list(uris))
            self._scheduler.wait_idle(timeout=600)
            return self._scheduler.stats().completed - initial

    def stats(self) -> dict:
        """Get cache and prefetch statistics.

        Returns:
            Dictionary with cache and prefetch stats
        """
        cache_stats = self._cache.stats()
        result = {
            "cache": {
                "total_bytes": cache_stats.total_bytes,
                "entry_count": cache_stats.entry_count,
                "hits": cache_stats.hits,
                "misses": cache_stats.misses,
            }
        }

        if self._scheduler is not None:
            scheduler_stats = self._scheduler.stats()
            result["prefetch"] = {
                "pending": scheduler_stats.pending,
                "completed": scheduler_stats.completed,
                "failed": scheduler_stats.failed,
                "workers_active": scheduler_stats.workers_active,
            }

        return result

    def gc(self, target_bytes: int) -> int:
        """Run garbage collection on cache.

        Args:
            target_bytes: Target cache size

        Returns:
            Bytes freed
        """
        return self._cache.gc(target_bytes)

    def _shutdown(self) -> None:
        """Shutdown prefetch scheduler."""
        if self._scheduler is not None:
            self._scheduler.stop()


# Global cache context (created on first use)
_global_context: CacheContext | None = None


def get_cache_context(
    cache_dir: Path | None = None,
    prefetch_mode: str = "off",
    **kwargs,
) -> CacheContext:
    """Get or create the global cache context.

    Args:
        cache_dir: Cache directory (uses default if not provided)
        prefetch_mode: Prefetch mode
        **kwargs: Additional arguments for CacheContext

    Returns:
        CacheContext instance
    """
    global _global_context

    if _global_context is None:
        from warpdatasets.config.settings import get_settings

        settings = get_settings()
        cache_dir = cache_dir or settings.cache_dir

        _global_context = CacheContext(
            cache_dir=cache_dir,
            prefetch_mode=prefetch_mode,
            **kwargs,
        )

    return _global_context


def reset_cache_context() -> None:
    """Reset the global cache context (for testing)."""
    global _global_context
    if _global_context is not None:
        _global_context._shutdown()
        _global_context = None
