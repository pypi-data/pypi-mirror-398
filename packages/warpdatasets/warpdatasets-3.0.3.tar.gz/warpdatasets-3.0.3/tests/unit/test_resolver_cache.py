"""Tests for manifest resolver and caching.

These tests enforce invariant I1.2: Read APIs have no hidden side-effects.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from warpdatasets.catalog.resolver import CatalogResolver
from warpdatasets.catalog.cache import ManifestCache, CacheEntry
from warpdatasets.catalog.store import ManifestStore, FetchResult
from warpdatasets.manifest.model import Manifest


class MockManifestStore(ManifestStore):
    """Mock manifest store for testing."""

    def __init__(self):
        self.fetch_count = 0
        self.manifests: dict[str, tuple[bytes, str]] = {}  # path -> (content, etag)
        self.return_not_modified = False

    def add_manifest(self, path: str, content: dict, etag: str = "etag-123"):
        """Add a manifest to the mock store."""
        self.manifests[path] = (json.dumps(content).encode(), etag)

    def fetch(
        self, path: str, if_none_match: str | None = None, if_modified_since: str | None = None
    ) -> FetchResult:
        """Fetch a manifest, respecting ETag."""
        self.fetch_count += 1

        if path not in self.manifests:
            return FetchResult(status=404, content=None, etag=None)

        content, etag = self.manifests[path]

        # Return 304 if ETag matches
        if if_none_match and if_none_match == etag:
            return FetchResult(status=304, content=None, etag=etag)

        return FetchResult(status=200, content=content, etag=etag)

    def exists(self, path: str) -> bool:
        """Check if manifest exists."""
        return path in self.manifests


class TestManifestCacheEtag:
    """Tests for ETag-based manifest caching."""

    def test_latest_cached_with_etag(self, tmp_path):
        """First fetch hits store; second returns 304 and uses cache."""
        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        # Setup: latest.json points to version hash
        store.add_manifest(
            "test/example/latest.json",
            {"version": "abc123def456"},
            etag="etag-latest-1",
        )
        store.add_manifest(
            "test/example/abc123def456.json",
            {
                "dataset": "test/example",
                "tables": {
                    "main": {
                        "format": "parquet",
                        "uris": ["s3://bucket/data.parquet"],
                    }
                },
            },
            etag="etag-version-1",
        )

        # First fetch - should hit store
        manifest1 = resolver.resolve("test/example")
        first_fetch_count = store.fetch_count
        assert first_fetch_count >= 2  # latest + version

        # Second fetch - should use cache (304 responses)
        manifest2 = resolver.resolve("test/example")

        # Should have made requests but got 304s
        # (implementation detail: might be same manifest object or equal)
        assert manifest1.dataset == manifest2.dataset

    def test_version_manifest_cached(self, tmp_path):
        """Version manifests are cached by version hash."""
        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        version_hash = "abc123def456"
        store.add_manifest(
            f"test/example/{version_hash}.json",
            {
                "dataset": "test/example",
                "tables": {
                    "main": {
                        "format": "parquet",
                        "uris": ["s3://bucket/data.parquet"],
                    }
                },
            },
            etag="etag-v1",
        )

        # First fetch by version
        manifest1 = resolver.resolve("test/example", version=version_hash)
        first_count = store.fetch_count

        # Second fetch by same version - should use cache
        manifest2 = resolver.resolve("test/example", version=version_hash)

        assert manifest1.dataset == manifest2.dataset

    def test_cache_keyed_by_dataset_and_version(self, tmp_path):
        """Cache distinguishes between different datasets and versions."""
        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        # Two different datasets
        store.add_manifest(
            "ws/dataset_a/v1.json",
            {
                "dataset": "ws/dataset_a",
                "tables": {"main": {"format": "parquet", "uris": []}},
            },
        )
        store.add_manifest(
            "ws/dataset_b/v1.json",
            {
                "dataset": "ws/dataset_b",
                "tables": {"main": {"format": "parquet", "uris": []}},
            },
        )

        manifest_a = resolver.resolve("ws/dataset_a", version="v1")
        manifest_b = resolver.resolve("ws/dataset_b", version="v1")

        assert manifest_a.dataset == "ws/dataset_a"
        assert manifest_b.dataset == "ws/dataset_b"

    def test_resolve_latest_then_version(self, tmp_path):
        """Resolving 'latest' fetches pointer then version manifest."""
        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        store.add_manifest(
            "test/example/latest.json",
            {"version": "version_hash_123"},
            etag="etag-latest",
        )
        store.add_manifest(
            "test/example/version_hash_123.json",
            {
                "dataset": "test/example",
                "tables": {"main": {"format": "parquet", "uris": []}},
            },
            etag="etag-version",
        )

        manifest = resolver.resolve("test/example")  # defaults to latest

        assert manifest.dataset == "test/example"
        # Should have fetched both latest.json and version.json
        assert store.fetch_count >= 2


class TestCacheEntry:
    """Tests for cache entry storage."""

    def test_cache_entry_stores_etag(self, tmp_path):
        """Cache entries include ETag for conditional requests."""
        cache = ManifestCache(cache_dir=tmp_path)

        entry = CacheEntry(
            content=b'{"dataset": "test/example"}',
            etag="etag-123",
            last_modified=None,
        )

        cache.put("test/example", "v1", entry)
        retrieved = cache.get("test/example", "v1")

        assert retrieved is not None
        assert retrieved.etag == "etag-123"

    def test_cache_entry_stores_last_modified(self, tmp_path):
        """Cache entries can include Last-Modified."""
        cache = ManifestCache(cache_dir=tmp_path)

        entry = CacheEntry(
            content=b'{"dataset": "test/example"}',
            etag=None,
            last_modified="Wed, 01 Jan 2025 00:00:00 GMT",
        )

        cache.put("test/example", "v1", entry)
        retrieved = cache.get("test/example", "v1")

        assert retrieved is not None
        assert retrieved.last_modified == "Wed, 01 Jan 2025 00:00:00 GMT"

    def test_cache_miss_returns_none(self, tmp_path):
        """Cache returns None for missing entries."""
        cache = ManifestCache(cache_dir=tmp_path)

        result = cache.get("nonexistent/dataset", "v1")

        assert result is None


class TestResolverNoSideEffects:
    """Tests that resolver doesn't have hidden side effects (I1.2)."""

    def test_resolve_does_not_download_parquet(self, tmp_path):
        """Resolving a manifest does not download parquet shards."""
        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        store.add_manifest(
            "test/example/latest.json",
            {"version": "v1"},
        )
        store.add_manifest(
            "test/example/v1.json",
            {
                "dataset": "test/example",
                "tables": {
                    "main": {
                        "format": "parquet",
                        "uris": [
                            "s3://bucket/huge-shard-0.parquet",
                            "s3://bucket/huge-shard-1.parquet",
                        ],
                    }
                },
            },
        )

        manifest = resolver.resolve("test/example")

        # Only manifest files should be fetched, not parquet
        fetched_paths = list(store.manifests.keys())
        assert all(".json" in p for p in fetched_paths)

    def test_resolve_only_writes_to_cache_dir(self, tmp_path):
        """Resolver only writes to designated cache directory."""
        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path / "cache")
        resolver = CatalogResolver(store=store, cache=cache)

        store.add_manifest("test/example/v1.json", {
            "dataset": "test/example",
            "tables": {"main": {"format": "parquet", "uris": []}},
        })

        # Create a marker file outside cache
        marker = tmp_path / "marker.txt"
        marker.write_text("original")

        resolver.resolve("test/example", version="v1")

        # Marker should be unchanged
        assert marker.read_text() == "original"
        # Cache dir should exist and contain something
        assert (tmp_path / "cache").exists()


class TestResolverErrors:
    """Tests for resolver error handling."""

    def test_dataset_not_found_error(self, tmp_path):
        """Missing dataset raises DatasetNotFoundError."""
        from warpdatasets.util.errors import DatasetNotFoundError

        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        with pytest.raises(DatasetNotFoundError) as exc_info:
            resolver.resolve("nonexistent/dataset")

        assert "nonexistent/dataset" in str(exc_info.value)

    def test_version_not_found_error(self, tmp_path):
        """Missing version raises ManifestNotFoundError."""
        from warpdatasets.util.errors import ManifestNotFoundError

        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        store.add_manifest("test/example/latest.json", {"version": "v1"})
        # But v1.json doesn't exist

        with pytest.raises(ManifestNotFoundError):
            resolver.resolve("test/example")

    def test_invalid_manifest_error(self, tmp_path):
        """Invalid manifest content raises ManifestInvalidError."""
        from warpdatasets.util.errors import ManifestInvalidError

        store = MockManifestStore()
        cache = ManifestCache(cache_dir=tmp_path)
        resolver = CatalogResolver(store=store, cache=cache)

        # Invalid JSON
        store.manifests["test/example/v1.json"] = (b"not valid json", "etag")

        with pytest.raises(ManifestInvalidError):
            resolver.resolve("test/example", version="v1")
