"""Integration tests for artifacts over HTTP.

Tests end-to-end flow: remote parquet -> ref column -> remote tar member -> decode
"""

from __future__ import annotations

import http.server
import io
import json
import socketserver
import tarfile
import threading
import time
from http.server import HTTPServer
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from warpdatasets.api.dataset import Dataset
from warpdatasets.catalog.cache import ManifestCache
from warpdatasets.catalog.resolver import CatalogResolver
from warpdatasets.catalog.stores.http import HttpManifestStore
from warpdatasets.config.settings import Settings
from warpdatasets.engines.duckdb import DuckDBEngine
from warpdatasets.manifest.model import Manifest


def create_dataset_from_server(http_server: dict, cache_path: Path, dataset_id: str = "test/dataset") -> Dataset:
    """Create a Dataset directly from test server config."""
    base_url = http_server["base_url"]

    settings = Settings(
        manifest_base=base_url,
        cache_dir=cache_path,
        mode="remote",
    )

    store = HttpManifestStore(base_url=f"{base_url}/manifests/")
    cache = ManifestCache(cache_dir=settings.cache_dir / "manifests")
    resolver = CatalogResolver(store=store, cache=cache)

    manifest = resolver.resolve(dataset_id)
    engine = DuckDBEngine(settings=settings)

    return Dataset(
        id=dataset_id,
        manifest=manifest,
        settings=settings,
        engine=engine,
    )


def create_test_tar(members: dict[str, bytes]) -> bytes:
    """Create a tar archive in memory with given members."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, content in members.items():
            data = io.BytesIO(content)
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tar.addfile(info, data)
    return buf.getvalue()


def create_test_png(width: int = 2, height: int = 2, color: tuple = (255, 0, 0)) -> bytes:
    """Create a minimal valid PNG image."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow required for image tests")

    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def http_artifact_server(tmp_path: Path):
    """Set up HTTP server with parquet + tar shards + manifest."""
    # Create test images
    red_png = create_test_png(2, 2, (255, 0, 0))
    green_png = create_test_png(2, 2, (0, 255, 0))
    blue_png = create_test_png(2, 2, (0, 0, 255))

    # Create tar shard with images
    tar_bytes = create_test_tar({
        "images/0.png": red_png,
        "images/1.png": green_png,
        "images/2.png": blue_png,
    })

    # Create parquet with image column referencing tar members
    table = pa.table({
        "id": [0, 1, 2],
        "image": ["images/0.png", "images/1.png", "images/2.png"],
        "label": ["red", "green", "blue"],
    })

    # Find an available port
    import socket
    import socketserver
    with socketserver.TCPServer(("localhost", 0), None) as temp_server:
        port = temp_server.server_address[1]

    base_url = f"http://localhost:{port}"

    # Create file structure matching expected paths
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    # Manifest path: warp/manifests/workspace/name/
    manifests_dir = tmp_path / "warp" / "manifests" / "test" / "dataset"
    manifests_dir.mkdir(parents=True)

    # Write parquet
    parquet_path = data_dir / "shard-0.parquet"
    pq.write_table(table, parquet_path)

    # Write tar
    tar_path = artifacts_dir / "images.tar"
    tar_path.write_bytes(tar_bytes)

    # Create manifest with version hash
    version_hash = "artifacts123456"
    manifest_dict = {
        "dataset": "test/dataset",
        "tables": {
            "main": {
                "format": "parquet",
                "shards": [{"uri": f"{base_url}/data/shard-0.parquet"}],
                "schema": {"id": "BIGINT", "image": "VARCHAR", "label": "VARCHAR"},
                "row_count": 3,
            }
        },
        "artifacts": {
            "raw_images": {
                "kind": "tar_shards",
                "shards": [{"uri": f"{base_url}/artifacts/images.tar"}],
                "compression": "none",
            }
        },
        "bindings": [
            {
                "table": "main",
                "column": "image",
                "artifact": "raw_images",
                "ref_type": "tar_member_path",
                "media_type": "image",
            }
        ],
    }

    # Write version manifest and latest pointer
    (manifests_dir / f"{version_hash}.json").write_text(json.dumps(manifest_dict))
    (manifests_dir / "latest.json").write_text(json.dumps({"version": version_hash}))

    # Start server with quiet handler
    import http.server

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmp_path), **kwargs)

        def log_message(self, format, *args):
            pass

    import time
    server = HTTPServer(("localhost", port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(0.1)  # Give server time to start

    yield {
        "port": port,
        "base_url": f"{base_url}/warp",
        "manifest_dict": manifest_dict,
        "red_png": red_png,
        "green_png": green_png,
        "blue_png": blue_png,
    }

    server.shutdown()


@pytest.mark.integration
class TestBatchDictsWrapRefs:
    """Tests for Table.batches with wrap_refs=True."""

    def test_batch_dicts_wrap_refs_returns_imageref(self, http_artifact_server, tmp_path):
        """wrap_refs=True returns ImageRef objects for bound columns."""
        from warpdatasets.refs.image import ImageRef

        ds = create_dataset_from_server(http_artifact_server, tmp_path / "cache")
        table = ds.table("main")

        batches = list(table.batches(as_format="dict", wrap_refs=True))

        assert len(batches) == 1
        batch = batches[0]

        # image column should contain ImageRef objects
        assert "image" in batch
        assert len(batch["image"]) == 3
        assert all(isinstance(ref, ImageRef) for ref in batch["image"])

    def test_image_ref_as_pil_roundtrip(self, http_artifact_server, tmp_path):
        """ImageRef.as_pil() returns correct image data."""
        pytest.importorskip("PIL")

        ds = create_dataset_from_server(http_artifact_server, tmp_path / "cache")
        table = ds.table("main")

        batches = list(table.batches(as_format="dict", wrap_refs=True))
        batch = batches[0]

        # Get the first image ref (should be red)
        img_ref = batch["image"][0]
        pil_img = img_ref.as_pil()

        assert pil_img.size == (2, 2)
        assert pil_img.mode == "RGB"
        # Check red pixel
        pixel = pil_img.getpixel((0, 0))
        assert pixel == (255, 0, 0)

    def test_ref_read_bytes_returns_correct_data(self, http_artifact_server, tmp_path):
        """FileRef.read_bytes() returns correct bytes."""
        green_png = http_artifact_server["green_png"]

        ds = create_dataset_from_server(http_artifact_server, tmp_path / "cache")
        table = ds.table("main")

        batches = list(table.batches(as_format="dict", wrap_refs=True))
        batch = batches[0]

        # Get the second image ref (should be green)
        img_ref = batch["image"][1]
        data = img_ref.read_bytes()

        assert data == green_png

    def test_non_bound_columns_unchanged(self, http_artifact_server, tmp_path):
        """Non-bound columns are passed through unchanged."""
        ds = create_dataset_from_server(http_artifact_server, tmp_path / "cache")
        table = ds.table("main")

        batches = list(table.batches(as_format="dict", wrap_refs=True))
        batch = batches[0]

        # id and label columns should be unchanged
        assert batch["id"] == [0, 1, 2]
        assert batch["label"] == ["red", "green", "blue"]

    def test_wrap_refs_requires_dict_format(self, http_artifact_server, tmp_path):
        """wrap_refs=True with arrow format raises ValueError."""
        ds = create_dataset_from_server(http_artifact_server, tmp_path / "cache")
        table = ds.table("main")

        with pytest.raises(ValueError) as exc_info:
            list(table.batches(as_format="arrow", wrap_refs=True))

        assert "dict" in str(exc_info.value)


@pytest.mark.integration
class TestRefMissingMember:
    """Tests for handling missing tar members."""

    @pytest.fixture
    def http_server_with_missing_ref(self, tmp_path: Path):
        """Set up server where parquet references non-existent tar member."""
        red_png = create_test_png(2, 2, (255, 0, 0))

        # Tar only has images/0.png
        tar_bytes = create_test_tar({
            "images/0.png": red_png,
        })

        # Parquet references images/0.png and images/missing.png
        table = pa.table({
            "id": [0, 1],
            "image": ["images/0.png", "images/missing.png"],
        })

        with socketserver.TCPServer(("localhost", 0), None) as temp_server:
            port = temp_server.server_address[1]

        base_url = f"http://localhost:{port}"

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manifests_dir = tmp_path / "warp" / "manifests" / "test" / "missing"
        manifests_dir.mkdir(parents=True)

        pq.write_table(table, data_dir / "shard-0.parquet")
        (artifacts_dir / "images.tar").write_bytes(tar_bytes)

        version_hash = "missing123456"
        manifest_dict = {
            "dataset": "test/missing",
            "tables": {
                "main": {
                    "format": "parquet",
                    "shards": [{"uri": f"{base_url}/data/shard-0.parquet"}],
                    "row_count": 2,
                }
            },
            "artifacts": {
                "raw_images": {
                    "kind": "tar_shards",
                    "shards": [{"uri": f"{base_url}/artifacts/images.tar"}],
                }
            },
            "bindings": [
                {
                    "table": "main",
                    "column": "image",
                    "artifact": "raw_images",
                    "ref_type": "tar_member_path",
                    "media_type": "image",
                }
            ],
        }

        (manifests_dir / f"{version_hash}.json").write_text(json.dumps(manifest_dict))
        (manifests_dir / "latest.json").write_text(json.dumps({"version": version_hash}))

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(tmp_path), **kwargs)

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("localhost", port), QuietHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.1)

        yield {"port": port, "base_url": f"{base_url}/warp"}

        server.shutdown()

    def test_ref_missing_raises_clear_error(self, http_server_with_missing_ref, tmp_path):
        """Missing ref raises RefNotFoundError with clear message."""
        from warpdatasets.util.errors import RefNotFoundError

        ds = create_dataset_from_server(
            http_server_with_missing_ref,
            tmp_path / "cache",
            dataset_id="test/missing",
        )
        table = ds.table("main")

        batches = list(table.batches(as_format="dict", wrap_refs=True))
        batch = batches[0]

        # First ref should work
        _ = batch["image"][0].read_bytes()

        # Second ref should fail with clear error
        with pytest.raises(RefNotFoundError) as exc_info:
            batch["image"][1].read_bytes()

        assert "missing.png" in str(exc_info.value)


@pytest.mark.integration
class TestShardingWithRefs:
    """Tests for sharding interaction with refs."""

    @pytest.fixture
    def http_server_multi_shard(self, tmp_path: Path):
        """Set up server with multiple parquet shards."""
        red_png = create_test_png(2, 2, (255, 0, 0))
        green_png = create_test_png(2, 2, (0, 255, 0))

        tar_bytes = create_test_tar({
            "images/0.png": red_png,
            "images/1.png": green_png,
        })

        # Two parquet shards
        shard0 = pa.table({
            "id": [0],
            "image": ["images/0.png"],
        })
        shard1 = pa.table({
            "id": [1],
            "image": ["images/1.png"],
        })

        with socketserver.TCPServer(("localhost", 0), None) as temp_server:
            port = temp_server.server_address[1]

        base_url = f"http://localhost:{port}"

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manifests_dir = tmp_path / "warp" / "manifests" / "test" / "sharded"
        manifests_dir.mkdir(parents=True)

        pq.write_table(shard0, data_dir / "shard-0.parquet")
        pq.write_table(shard1, data_dir / "shard-1.parquet")
        (artifacts_dir / "images.tar").write_bytes(tar_bytes)

        version_hash = "multishard123456"
        manifest_dict = {
            "dataset": "test/sharded",
            "tables": {
                "main": {
                    "format": "parquet",
                    "shards": [
                        {"uri": f"{base_url}/data/shard-0.parquet"},
                        {"uri": f"{base_url}/data/shard-1.parquet"},
                    ],
                    "row_count": 2,
                }
            },
            "artifacts": {
                "raw_images": {
                    "kind": "tar_shards",
                    "shards": [{"uri": f"{base_url}/artifacts/images.tar"}],
                }
            },
            "bindings": [
                {
                    "table": "main",
                    "column": "image",
                    "artifact": "raw_images",
                    "ref_type": "tar_member_path",
                    "media_type": "image",
                }
            ],
        }

        (manifests_dir / f"{version_hash}.json").write_text(json.dumps(manifest_dict))
        (manifests_dir / "latest.json").write_text(json.dumps({"version": version_hash}))

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(tmp_path), **kwargs)

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("localhost", port), QuietHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.1)

        yield {"port": port, "base_url": f"{base_url}/warp"}

        server.shutdown()

    def test_refs_resolve_with_sharding(self, http_server_multi_shard, tmp_path):
        """Refs still resolve when reading subset of parquet shards."""
        pytest.importorskip("PIL")

        ds = create_dataset_from_server(
            http_server_multi_shard,
            tmp_path / "cache",
            dataset_id="test/sharded",
        )
        table = ds.table("main")

        # Worker 0 of 2: gets shard 0
        batches = list(table.batches(
            as_format="dict",
            wrap_refs=True,
            shard=(0, 2),
        ))

        assert len(batches) == 1
        batch = batches[0]
        assert len(batch["image"]) == 1

        # Should resolve successfully
        img = batch["image"][0].as_pil()
        assert img.size == (2, 2)
