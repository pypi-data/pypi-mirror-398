"""Manifest cache with ETag/Last-Modified support."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CacheEntry:
    """A cached manifest entry."""

    content: bytes
    etag: str | None = None
    last_modified: str | None = None


class ManifestCache:
    """Local cache for manifest files.

    Caches manifests by (dataset_id, version) with ETag/Last-Modified
    for conditional requests.
    """

    def __init__(self, cache_dir: Path | str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, dataset_id: str, version: str) -> str:
        """Generate a safe cache key from dataset ID and version."""
        # Use hash to avoid filesystem issues with special characters
        key_str = f"{dataset_id}:{version}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def _entry_path(self, dataset_id: str, version: str) -> Path:
        """Get the path for a cache entry."""
        key = self._cache_key(dataset_id, version)
        return self.cache_dir / f"{key}.json"

    def _meta_path(self, dataset_id: str, version: str) -> Path:
        """Get the path for cache entry metadata."""
        key = self._cache_key(dataset_id, version)
        return self.cache_dir / f"{key}.meta.json"

    def get(self, dataset_id: str, version: str) -> CacheEntry | None:
        """Get a cached manifest entry.

        Args:
            dataset_id: Dataset identifier (workspace/name)
            version: Version hash or "latest"

        Returns:
            CacheEntry if cached, None otherwise
        """
        entry_path = self._entry_path(dataset_id, version)
        meta_path = self._meta_path(dataset_id, version)

        if not entry_path.exists():
            return None

        try:
            content = entry_path.read_bytes()

            etag = None
            last_modified = None
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                etag = meta.get("etag")
                last_modified = meta.get("last_modified")

            return CacheEntry(
                content=content,
                etag=etag,
                last_modified=last_modified,
            )
        except (IOError, json.JSONDecodeError):
            return None

    def put(
        self,
        dataset_id: str,
        version: str,
        entry: CacheEntry,
    ) -> None:
        """Store a manifest entry in the cache.

        Args:
            dataset_id: Dataset identifier (workspace/name)
            version: Version hash or "latest"
            entry: The cache entry to store
        """
        entry_path = self._entry_path(dataset_id, version)
        meta_path = self._meta_path(dataset_id, version)

        try:
            entry_path.write_bytes(entry.content)

            meta = {}
            if entry.etag:
                meta["etag"] = entry.etag
            if entry.last_modified:
                meta["last_modified"] = entry.last_modified

            if meta:
                meta_path.write_text(json.dumps(meta))
            elif meta_path.exists():
                meta_path.unlink()

        except IOError:
            # Cache write failure is not fatal
            pass

    def invalidate(self, dataset_id: str, version: str) -> None:
        """Remove a cached entry.

        Args:
            dataset_id: Dataset identifier (workspace/name)
            version: Version hash or "latest"
        """
        entry_path = self._entry_path(dataset_id, version)
        meta_path = self._meta_path(dataset_id, version)

        try:
            if entry_path.exists():
                entry_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
        except IOError:
            pass

    def clear(self) -> None:
        """Clear all cached entries."""
        try:
            for path in self.cache_dir.glob("*.json"):
                path.unlink()
        except IOError:
            pass
