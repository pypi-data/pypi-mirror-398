"""Integration tests for HTTP remote parquet streaming.

These tests verify:
- I2.1: Streaming is remote-first and does not require prefetch/pull
- I2.2: Sharding is deterministic and non-overlapping
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
def multi_shard_http_server(tmp_path):
    """Start HTTP server with multiple parquet shards."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create 6 parquet shards with known data
    total_rows = 0
    shard_info = []

    for shard_idx in range(6):
        # Each shard has unique shard_id values
        start_id = shard_idx * 100
        ids = list(range(start_id, start_id + 50))  # 50 rows per shard
        table = pa.table({
            "id": pa.array(ids),
            "shard_id": pa.array([shard_idx] * 50),
            "value": pa.array([f"value_{i}" for i in ids]),
            "score": pa.array([float(i) / 10 for i in ids]),
        })
        parquet_path = data_dir / f"part-{shard_idx:04d}.parquet"
        pq.write_table(table, parquet_path)
        total_rows += 50
        shard_info.append({"shard_idx": shard_idx, "rows": 50, "start_id": start_id})

    # Find available port
    with socketserver.TCPServer(("localhost", 0), None) as temp_server:
        port = temp_server.server_address[1]

    # Create manifest
    manifests_dir = tmp_path / "warp" / "manifests" / "test" / "sharded"
    manifests_dir.mkdir(parents=True)

    version_hash = "sharded123456"
    version_manifest = {
        "dataset": "test/sharded",
        "tables": {
            "main": {
                "format": "parquet",
                "shards": [
                    {"uri": f"http://localhost:{port}/data/part-{i:04d}.parquet"}
                    for i in range(6)
                ],
                "schema": {
                    "id": "BIGINT",
                    "shard_id": "BIGINT",
                    "value": "VARCHAR",
                    "score": "DOUBLE",
                },
                "row_count": total_rows,
            }
        },
    }
    (manifests_dir / f"{version_hash}.json").write_text(json.dumps(version_manifest))
    (manifests_dir / "latest.json").write_text(json.dumps({"version": version_hash}))

    # Create handler
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmp_path), **kwargs)

        def log_message(self, format, *args):
            pass

    # Start server
    httpd = socketserver.TCPServer(("localhost", port), QuietHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)

    yield {
        "port": port,
        "base_url": f"http://localhost:{port}/warp",
        "tmp_path": tmp_path,
        "total_rows": total_rows,
        "num_shards": 6,
        "shard_info": shard_info,
    }

    httpd.shutdown()


def create_dataset(http_server, cache_path) -> Dataset:
    """Helper to create a dataset from the test server."""
    settings = Settings(
        manifest_base=http_server["base_url"],
        cache_dir=cache_path,
        mode="remote",
    )

    store = HttpManifestStore(base_url=f"{http_server['base_url']}/manifests/")
    cache = ManifestCache(cache_dir=settings.cache_dir / "manifests")
    resolver = CatalogResolver(store=store, cache=cache)

    manifest = resolver.resolve("test/sharded")
    engine = DuckDBEngine(settings=settings)

    return Dataset(
        id="test/sharded",
        manifest=manifest,
        settings=settings,
        engine=engine,
    )


@pytest.mark.integration
class TestStreamingBasic:
    """Basic streaming functionality tests."""

    def test_stream_yields_arrow_batches(self, multi_shard_http_server, tmp_path):
        """batches() yields pyarrow.RecordBatch objects."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        batches = list(ds.table("main").batches(batch_size=100))

        assert len(batches) > 0
        assert all(isinstance(b, pa.RecordBatch) for b in batches)

    def test_stream_reads_all_rows_single_worker(self, multi_shard_http_server, tmp_path):
        """Without sharding, all rows are read."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        total_rows = 0
        for batch in ds.table("main").batches(batch_size=100):
            total_rows += batch.num_rows

        assert total_rows == multi_shard_http_server["total_rows"]

    def test_stream_respects_batch_size(self, multi_shard_http_server, tmp_path):
        """Batches have at most batch_size rows."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        batch_size = 30
        for batch in ds.table("main").batches(batch_size=batch_size):
            assert batch.num_rows <= batch_size

    def test_stream_with_limit(self, multi_shard_http_server, tmp_path):
        """limit parameter restricts total rows."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        total_rows = 0
        for batch in ds.table("main").batches(batch_size=50, limit=75):
            total_rows += batch.num_rows

        assert total_rows == 75


@pytest.mark.integration
class TestStreamingSharding:
    """Sharding correctness tests."""

    def test_stream_sharding_no_overlap(self, multi_shard_http_server, tmp_path):
        """Different ranks get non-overlapping data."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        # Collect shard_ids seen by each rank
        rank0_shards = set()
        rank1_shards = set()

        for batch in ds.table("main").batches(batch_size=100, shard=(0, 2)):
            rank0_shards.update(batch.column("shard_id").to_pylist())

        for batch in ds.table("main").batches(batch_size=100, shard=(1, 2)):
            rank1_shards.update(batch.column("shard_id").to_pylist())

        # No overlap
        assert rank0_shards.isdisjoint(rank1_shards), \
            f"Overlap found: {rank0_shards & rank1_shards}"

    def test_stream_sharding_full_coverage(self, multi_shard_http_server, tmp_path):
        """Union of ranks covers all data."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        all_ids = set()
        for rank in range(3):
            for batch in ds.table("main").batches(batch_size=100, shard=(rank, 3)):
                all_ids.update(batch.column("id").to_pylist())

        # Should have all IDs from 0-299 (6 shards * 50 rows)
        expected_ids = set()
        for info in multi_shard_http_server["shard_info"]:
            expected_ids.update(range(info["start_id"], info["start_id"] + info["rows"]))

        assert all_ids == expected_ids

    def test_stream_sharding_total_rows_preserved(self, multi_shard_http_server, tmp_path):
        """Total rows across all ranks equals original total."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        total_across_ranks = 0
        for rank in range(4):
            for batch in ds.table("main").batches(batch_size=100, shard=(rank, 4)):
                total_across_ranks += batch.num_rows

        assert total_across_ranks == multi_shard_http_server["total_rows"]


@pytest.mark.integration
class TestStreamingProjection:
    """Column projection tests."""

    def test_projection_returns_only_requested_columns(self, multi_shard_http_server, tmp_path):
        """Only requested columns are returned."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        for batch in ds.table("main").batches(batch_size=100, columns=["id", "score"]):
            assert set(batch.schema.names) == {"id", "score"}

    def test_projection_preserves_data(self, multi_shard_http_server, tmp_path):
        """Projected data is correct."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        all_ids = []
        for batch in ds.table("main").batches(batch_size=100, columns=["id"]):
            all_ids.extend(batch.column("id").to_pylist())

        # Should have same IDs as full read
        all_ids_full = []
        for batch in ds.table("main").batches(batch_size=100):
            all_ids_full.extend(batch.column("id").to_pylist())

        assert sorted(all_ids) == sorted(all_ids_full)


@pytest.mark.integration
class TestStreamingDictFormat:
    """Dict format output tests."""

    def test_dict_format_returns_dict(self, multi_shard_http_server, tmp_path):
        """as_format='dict' yields dict-of-lists."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        for batch in ds.table("main").batches(batch_size=100, as_format="dict"):
            assert isinstance(batch, dict)
            assert "id" in batch
            assert isinstance(batch["id"], list)
            break  # Just test first batch

    def test_dict_format_has_all_columns(self, multi_shard_http_server, tmp_path):
        """Dict batches have all columns."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        for batch in ds.table("main").batches(batch_size=100, as_format="dict"):
            assert set(batch.keys()) == {"id", "shard_id", "value", "score"}
            break


@pytest.mark.integration
class TestStreamingNoSideEffects:
    """Tests that streaming doesn't have hidden side effects."""

    def test_streaming_does_not_cache_parquet(self, multi_shard_http_server, tmp_path):
        """Streaming doesn't download parquet files to cache."""
        cache_dir = tmp_path / "cache"
        ds = create_dataset(multi_shard_http_server, cache_dir)

        # Stream all data
        for batch in ds.table("main").batches(batch_size=100):
            pass

        # Check cache - should only have manifest files
        if cache_dir.exists():
            all_files = list(cache_dir.rglob("*"))
            parquet_files = [f for f in all_files if f.suffix == ".parquet"]
            assert len(parquet_files) == 0, "Parquet files should not be cached"


@pytest.mark.integration
class TestDatasetStreamConvenience:
    """Tests for Dataset.stream() convenience method."""

    def test_dataset_stream_method(self, multi_shard_http_server, tmp_path):
        """Dataset.stream() works as shorthand."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        total_rows = 0
        for batch in ds.stream(batch_size=100):
            total_rows += batch.num_rows

        assert total_rows == multi_shard_http_server["total_rows"]

    def test_dataset_stream_with_table_name(self, multi_shard_http_server, tmp_path):
        """Dataset.stream() accepts table parameter."""
        ds = create_dataset(multi_shard_http_server, tmp_path / "cache")

        total_rows = 0
        for batch in ds.stream(table="main", batch_size=100):
            total_rows += batch.num_rows

        assert total_rows == multi_shard_http_server["total_rows"]
