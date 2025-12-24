"""Integration tests for remote HTTP parquet access.

These tests verify that the entire stack works end-to-end:
- Manifest resolution over HTTP
- Schema retrieval without full download
- Head queries via DuckDB httpfs
"""

import http.server
import json
import socketserver
import threading
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from warpdatasets.config.settings import Settings
from warpdatasets.catalog.stores.http import HttpManifestStore
from warpdatasets.catalog.cache import ManifestCache
from warpdatasets.catalog.resolver import CatalogResolver
from warpdatasets.engines.duckdb import DuckDBEngine
from warpdatasets.api.dataset import Dataset


@pytest.fixture
def http_server(tmp_path):
    """Start a local HTTP server serving test files."""
    # Create test data
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create parquet shard
    table = pa.table({
        "id": pa.array([1, 2, 3, 4, 5]),
        "name": pa.array(["alice", "bob", "charlie", "diana", "eve"]),
        "score": pa.array([95.5, 87.3, 92.1, 78.9, 88.6]),
    })
    parquet_path = data_dir / "part-0000.parquet"
    pq.write_table(table, parquet_path)

    # Find available port first
    with socketserver.TCPServer(("localhost", 0), None) as temp_server:
        port = temp_server.server_address[1]

    # Create manifest structure with the known port
    manifests_dir = tmp_path / "warp" / "manifests" / "test" / "example"
    manifests_dir.mkdir(parents=True)

    version_hash = "abc123def456"
    version_manifest = {
        "dataset": "test/example",
        "tables": {
            "main": {
                "format": "parquet",
                "shards": [{"uri": f"http://localhost:{port}/data/part-0000.parquet"}],
                "schema": {"id": "BIGINT", "name": "VARCHAR", "score": "DOUBLE"},
                "row_count": 5,
            }
        },
    }
    (manifests_dir / f"{version_hash}.json").write_text(json.dumps(version_manifest))

    # Latest pointer
    latest = {"version": version_hash}
    (manifests_dir / "latest.json").write_text(json.dumps(latest))

    # Create handler class
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmp_path), **kwargs)

        def log_message(self, format, *args):
            pass  # Suppress logging

    # Start server on the pre-determined port
    httpd = socketserver.TCPServer(("localhost", port), QuietHandler)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Give server time to start
    time.sleep(0.1)

    yield {
        "port": port,
        "base_url": f"http://localhost:{port}/warp",
        "tmp_path": tmp_path,
    }

    httpd.shutdown()


@pytest.mark.integration
def test_remote_schema_over_http(http_server, tmp_path):
    """Schema retrieval works over HTTP without downloading full shards."""
    # Configure settings
    settings = Settings(
        manifest_base=http_server["base_url"],
        cache_dir=tmp_path / "cache",
        mode="remote",
    )

    # Create resolver manually
    store = HttpManifestStore(base_url=f"{http_server['base_url']}/manifests/")
    cache = ManifestCache(cache_dir=settings.cache_dir / "manifests")
    resolver = CatalogResolver(store=store, cache=cache)

    # Resolve manifest
    manifest = resolver.resolve("test/example")

    # Create dataset manually
    engine = DuckDBEngine(settings=settings)
    ds = Dataset(
        id="test/example",
        manifest=manifest,
        settings=settings,
        engine=engine,
    )

    # Get schema
    schema = ds.table("main").schema()

    assert "id" in schema
    assert "name" in schema
    assert "score" in schema


@pytest.mark.integration
def test_remote_head_over_http(http_server, tmp_path):
    """Head query works over HTTP via DuckDB httpfs."""
    settings = Settings(
        manifest_base=http_server["base_url"],
        cache_dir=tmp_path / "cache",
        mode="remote",
    )

    store = HttpManifestStore(base_url=f"{http_server['base_url']}/manifests/")
    cache = ManifestCache(cache_dir=settings.cache_dir / "manifests")
    resolver = CatalogResolver(store=store, cache=cache)

    manifest = resolver.resolve("test/example")
    engine = DuckDBEngine(settings=settings)
    ds = Dataset(
        id="test/example",
        manifest=manifest,
        settings=settings,
        engine=engine,
    )

    # Get head
    head_relation = ds.table("main").head(3)
    df = head_relation.df()

    assert len(df) == 3
    assert "id" in df.columns
    assert "name" in df.columns


@pytest.mark.integration
def test_no_full_download_side_effect(http_server, tmp_path):
    """Resolving and querying schema doesn't cache full parquet files."""
    cache_dir = tmp_path / "cache"
    settings = Settings(
        manifest_base=http_server["base_url"],
        cache_dir=cache_dir,
        mode="remote",
    )

    store = HttpManifestStore(base_url=f"{http_server['base_url']}/manifests/")
    cache = ManifestCache(cache_dir=settings.cache_dir / "manifests")
    resolver = CatalogResolver(store=store, cache=cache)

    manifest = resolver.resolve("test/example")
    engine = DuckDBEngine(settings=settings)
    ds = Dataset(
        id="test/example",
        manifest=manifest,
        settings=settings,
        engine=engine,
    )

    # Just get schema and head
    ds.table("main").schema()
    ds.table("main").head(2)

    # Check cache directory - should only have manifest JSON files
    if cache_dir.exists():
        all_files = list(cache_dir.rglob("*"))
        parquet_files = [f for f in all_files if f.suffix == ".parquet"]
        assert len(parquet_files) == 0, "Parquet files should not be cached by resolve/schema/head"


@pytest.mark.integration
def test_filtered_query_remote(http_server, tmp_path):
    """Filtered queries work remotely."""
    settings = Settings(
        manifest_base=http_server["base_url"],
        cache_dir=tmp_path / "cache",
        mode="remote",
    )

    store = HttpManifestStore(base_url=f"{http_server['base_url']}/manifests/")
    cache = ManifestCache(cache_dir=settings.cache_dir / "manifests")
    resolver = CatalogResolver(store=store, cache=cache)

    manifest = resolver.resolve("test/example")
    engine = DuckDBEngine(settings=settings)
    ds = Dataset(
        id="test/example",
        manifest=manifest,
        settings=settings,
        engine=engine,
    )

    # Filter query
    result = ds.table("main").filter("score > 90")
    df = result.df()

    assert len(df) == 2  # alice (95.5) and charlie (92.1)
    assert all(df["score"] > 90)
