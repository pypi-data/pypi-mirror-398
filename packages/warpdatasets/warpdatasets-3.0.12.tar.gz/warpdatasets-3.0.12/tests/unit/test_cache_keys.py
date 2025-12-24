"""Tests for cache key generation and stability.

Tests Phase 4 invariant I4.3: Cache is content-addressed.
"""

from __future__ import annotations

import pytest


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_same_uri_same_etag_same_key(self):
        """Same URI + same etag produces same key."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/path/shard-0.parquet"
        etag = '"abc123"'

        key1 = compute_cache_key(uri, etag=etag)
        key2 = compute_cache_key(uri, etag=etag)

        assert key1 == key2

    def test_different_etag_different_key(self):
        """Same URI + different etag produces different key."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/path/shard-0.parquet"

        key1 = compute_cache_key(uri, etag='"abc123"')
        key2 = compute_cache_key(uri, etag='"def456"')

        assert key1 != key2

    def test_different_uri_different_key(self):
        """Different URIs produce different keys."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        etag = '"abc123"'

        key1 = compute_cache_key("s3://bucket/shard-0.parquet", etag=etag)
        key2 = compute_cache_key("s3://bucket/shard-1.parquet", etag=etag)

        assert key1 != key2

    def test_size_fallback_stable(self):
        """URI + size produces stable key when no etag."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/shard-0.parquet"
        size = 12345678

        key1 = compute_cache_key(uri, size=size)
        key2 = compute_cache_key(uri, size=size)

        assert key1 == key2

    def test_different_size_different_key(self):
        """Different sizes produce different keys."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/shard-0.parquet"

        key1 = compute_cache_key(uri, size=1000)
        key2 = compute_cache_key(uri, size=2000)

        assert key1 != key2

    def test_etag_takes_precedence_over_size(self):
        """When etag is provided, size is ignored for key."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/shard-0.parquet"
        etag = '"abc123"'

        key1 = compute_cache_key(uri, etag=etag, size=1000)
        key2 = compute_cache_key(uri, etag=etag, size=2000)

        assert key1 == key2  # Size doesn't matter when etag is present

    def test_uri_only_fallback(self):
        """URI-only key is stable but least preferred."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/shard-0.parquet"

        key1 = compute_cache_key(uri)
        key2 = compute_cache_key(uri)

        assert key1 == key2

    def test_key_is_valid_filename(self):
        """Cache key is a valid filename (hex string)."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/path/with spaces/shard-0.parquet"
        key = compute_cache_key(uri, etag='"abc"')

        # Should be hex string (64 chars for sha256)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)


class TestCacheKeyFromMeta:
    """Tests for computing cache key from metadata dict."""

    def test_from_meta_with_etag(self):
        """Compute key from metadata containing etag."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/shard-0.parquet"
        meta = {"etag": '"abc123"', "size": 1000}

        key = compute_cache_key(uri, etag=meta.get("etag"), size=meta.get("size"))

        # Verify it matches direct call
        assert key == compute_cache_key(uri, etag='"abc123"')

    def test_from_meta_without_etag(self):
        """Compute key from metadata without etag."""
        from warpdatasets.cache.blob_cache import compute_cache_key

        uri = "s3://bucket/shard-0.parquet"
        meta = {"size": 1000, "last_modified": "2024-01-01"}

        key = compute_cache_key(uri, size=meta.get("size"))

        assert key == compute_cache_key(uri, size=1000)
