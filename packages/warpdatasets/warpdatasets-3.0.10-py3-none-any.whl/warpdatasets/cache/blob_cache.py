"""Content-addressed blob cache for table and artifact shards.

Provides atomic writes, LRU eviction, and statistics tracking.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


def compute_cache_key(
    uri: str,
    *,
    etag: str | None = None,
    size: int | None = None,
) -> str:
    """Compute cache key from URI and validation token.

    Priority:
    1. URI + etag (if etag provided)
    2. URI + size (if size provided, no etag)
    3. URI only (fallback)

    Args:
        uri: The resource URI
        etag: Optional ETag from server
        size: Optional content size

    Returns:
        64-character hex string (sha256)
    """
    if etag is not None:
        # ETag takes precedence
        token = f"{uri}|etag:{etag}"
    elif size is not None:
        token = f"{uri}|size:{size}"
    else:
        token = uri

    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class CacheStats:
    """Cache statistics."""

    total_bytes: int = 0
    entry_count: int = 0
    hits: int = 0
    misses: int = 0
    pending: int = 0
    completed: int = 0
    failed: int = 0


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""

    key: str
    path: Path
    size: int
    mtime: float
    meta: dict


class BlobCache:
    """Content-addressed local cache for blob data.

    Stores blobs with atomic writes and LRU eviction.

    Directory structure:
        cache_dir/
            objects/ab/cd/<key>      # blob data
            meta/ab/cd/<key>.json    # metadata
    """

    def __init__(
        self,
        cache_dir: Path | str,
        max_size_bytes: int | None = None,
    ):
        """Initialize blob cache.

        Args:
            cache_dir: Directory for cache storage
            max_size_bytes: Maximum cache size (None for unlimited)
        """
        self._cache_dir = Path(cache_dir)
        self._objects_dir = self._cache_dir / "objects"
        self._meta_dir = self._cache_dir / "meta"
        self._max_size = max_size_bytes

        # Create directories
        self._objects_dir.mkdir(parents=True, exist_ok=True)
        self._meta_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self._stats_lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def _key_path(self, key: str, base_dir: Path, suffix: str = "") -> Path:
        """Get path for a cache key."""
        return base_dir / key[:2] / key[2:4] / f"{key}{suffix}"

    def _object_path(self, key: str) -> Path:
        """Get object file path for key."""
        return self._key_path(key, self._objects_dir)

    def _meta_path(self, key: str) -> Path:
        """Get metadata file path for key."""
        return self._key_path(key, self._meta_dir, ".json")

    def has(self, key: str) -> bool:
        """Check if key is cached (object and metadata exist).

        Args:
            key: Cache key

        Returns:
            True if cached and complete
        """
        obj_path = self._object_path(key)
        meta_path = self._meta_path(key)

        # Both must exist for complete cache entry
        exists = obj_path.exists() and meta_path.exists()

        # Track hit/miss for get_path calls
        # has() doesn't count as access

        return exists

    def get_path(self, key: str) -> Path | None:
        """Get local path for cached object.

        Args:
            key: Cache key

        Returns:
            Path to cached file, or None if not cached
        """
        with self._stats_lock:
            if self.has(key):
                self._hits += 1
                return self._object_path(key)
            else:
                self._misses += 1
                return None

    def put(
        self,
        key: str,
        tmp_path: Path,
        meta: dict,
    ) -> Path:
        """Store blob in cache atomically.

        Args:
            key: Cache key
            tmp_path: Temporary file with content (will be moved)
            meta: Metadata dict (uri, size, etag, etc.)

        Returns:
            Path to cached object
        """
        obj_path = self._object_path(key)
        meta_path = self._meta_path(key)

        # Create parent directories
        obj_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.parent.mkdir(parents=True, exist_ok=True)

        # Move object file atomically (on same filesystem)
        shutil.move(str(tmp_path), str(obj_path))

        # Write metadata
        meta_path.write_text(json.dumps(meta))

        # Trigger eviction if over limit
        if self._max_size is not None:
            self._maybe_evict()

        return obj_path

    def touch(self, key: str) -> None:
        """Update access time for LRU tracking.

        Args:
            key: Cache key
        """
        obj_path = self._object_path(key)
        if obj_path.exists():
            # Update mtime
            os.utime(obj_path, None)

    def stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats with current counts
        """
        total_bytes = 0
        entry_count = 0

        # Scan objects directory
        if self._objects_dir.exists():
            for obj_path in self._objects_dir.rglob("*"):
                if obj_path.is_file() and not obj_path.name.endswith(".json"):
                    # Check corresponding meta exists
                    key = obj_path.name
                    meta_path = self._meta_path(key)
                    if meta_path.exists():
                        try:
                            total_bytes += obj_path.stat().st_size
                            entry_count += 1
                        except OSError:
                            pass

        with self._stats_lock:
            return CacheStats(
                total_bytes=total_bytes,
                entry_count=entry_count,
                hits=self._hits,
                misses=self._misses,
            )

    def gc(self, target_bytes: int) -> int:
        """Garbage collect to reach target size.

        Removes oldest entries until size is at or below target.

        Args:
            target_bytes: Target cache size in bytes

        Returns:
            Number of bytes freed
        """
        entries = self._list_entries_by_mtime()

        if not entries:
            return 0

        current_size = sum(e.size for e in entries)
        if current_size <= target_bytes:
            return 0

        freed = 0
        # Remove oldest first (entries are sorted oldest to newest)
        for entry in entries:
            if current_size <= target_bytes:
                break

            try:
                entry.path.unlink()
                self._meta_path(entry.key).unlink()
                freed += entry.size
                current_size -= entry.size
            except OSError:
                pass

        return freed

    def _maybe_evict(self) -> None:
        """Check cache size and evict if needed."""
        if self._max_size is None:
            return

        current = self.stats().total_bytes
        if current > self._max_size:
            # Evict to 90% of max to avoid constant eviction
            target = int(self._max_size * 0.9)
            self.gc(target)

    def _list_entries_by_mtime(self) -> list[CacheEntry]:
        """List all cache entries sorted by mtime (oldest first)."""
        entries = []

        if not self._objects_dir.exists():
            return entries

        for obj_path in self._objects_dir.rglob("*"):
            if obj_path.is_file():
                key = obj_path.name
                meta_path = self._meta_path(key)

                if meta_path.exists():
                    try:
                        stat = obj_path.stat()
                        meta = json.loads(meta_path.read_text())
                        entries.append(CacheEntry(
                            key=key,
                            path=obj_path,
                            size=stat.st_size,
                            mtime=stat.st_mtime,
                            meta=meta,
                        ))
                    except (OSError, json.JSONDecodeError):
                        pass

        # Sort by mtime (oldest first)
        entries.sort(key=lambda e: e.mtime)
        return entries
