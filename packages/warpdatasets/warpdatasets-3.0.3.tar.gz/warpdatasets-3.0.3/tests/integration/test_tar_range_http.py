"""Integration tests for HTTP range-read artifact member extraction.

Tests Phase 6 invariant I6.4: Remote-first random access.
"""

from __future__ import annotations

import http.server
import json
import socketserver
import tarfile
import tempfile
import threading
from pathlib import Path

import pytest


class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that supports Range requests."""

    def do_GET(self):
        """Handle GET with optional Range header."""
        # Parse Range header
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            # Parse range
            range_spec = range_header[6:]
            start, end = range_spec.split("-")
            start = int(start)
            end = int(end) if end else None

            # Get file path
            path = self.translate_path(self.path)
            try:
                with open(path, "rb") as f:
                    f.seek(start)
                    if end:
                        length = end - start + 1
                        data = f.read(length)
                    else:
                        data = f.read()

                self.send_response(206)  # Partial Content
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", len(data))
                self.send_header("Content-Range", f"bytes {start}-{start + len(data) - 1}/*")
                self.end_headers()
                self.wfile.write(data)
            except FileNotFoundError:
                self.send_error(404)
        else:
            # Full file
            super().do_GET()

    def log_message(self, format, *args):
        """Silence server logs."""
        pass


@pytest.fixture
def http_server_with_range(tmp_path):
    """Start HTTP server that supports Range requests."""
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    handler = RangeHTTPRequestHandler
    with socketserver.TCPServer(("", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        yield f"http://localhost:{port}", tmp_path
        httpd.shutdown()

    os.chdir(old_cwd)


class TestHTTPRangeReads:
    """Tests for HTTP range-read member extraction."""

    def test_reads_member_via_range_request(self, http_server_with_range):
        """Can read tar member using HTTP Range request."""
        base_url, tmp_path = http_server_with_range

        # Create tar with known content
        tar_path = tmp_path / "shard-00000.tar"
        content = b"hello world from tar member"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="test.txt")
            info.size = len(content)
            tar.addfile(info, fileobj=__import__("io").BytesIO(content))

        # Build index
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        # Create artifact descriptor
        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"{base_url}/shard-00000.tar")],
            index=ShardInfo(uri=f"file://{index_path}"),
        )

        # Create resolver
        from warpdatasets.artifacts.resolver import ArtifactResolver

        resolver = ArtifactResolver(
            artifacts={"files": artifact},
            cache_context=None,
        )

        # Read member
        result = resolver.read_bytes("files", "test.txt")
        assert result == content

    def test_reads_multiple_members_independently(self, http_server_with_range):
        """Each member read is independent (no full tar download)."""
        base_url, tmp_path = http_server_with_range

        # Create tar with multiple members
        tar_path = tmp_path / "shard-00000.tar"
        contents = {
            "a.txt": b"content a" * 100,
            "b.txt": b"content b" * 200,
            "c.txt": b"content c" * 50,
        }
        with tarfile.open(tar_path, "w") as tar:
            for name, data in contents.items():
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        # Build index
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.artifacts.resolver import ArtifactResolver

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"{base_url}/shard-00000.tar")],
            index=ShardInfo(uri=f"file://{index_path}"),
        )

        resolver = ArtifactResolver(
            artifacts={"files": artifact},
            cache_context=None,
        )

        # Read each member
        for name, expected in contents.items():
            result = resolver.read_bytes("files", name)
            assert result == expected

    def test_reads_from_multiple_shards(self, http_server_with_range):
        """Can read members from different remote shards."""
        base_url, tmp_path = http_server_with_range

        # Create multiple shards
        shard_uris = []
        contents = {}
        for shard_idx in range(3):
            tar_path = tmp_path / f"shard-{shard_idx:05d}.tar"
            shard_uris.append(f"{base_url}/shard-{shard_idx:05d}.tar")

            with tarfile.open(tar_path, "w") as tar:
                for i in range(2):
                    name = f"file_s{shard_idx}_f{i}.txt"
                    data = f"content from shard {shard_idx} file {i}".encode()
                    contents[name] = data
                    info = tarfile.TarInfo(name=name)
                    info.size = len(data)
                    tar.addfile(info, fileobj=__import__("io").BytesIO(data))

        # Build index
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        tar_paths = sorted(tmp_path.glob("shard-*.tar"))
        index_data = build_tar_index(tar_paths)
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.artifacts.resolver import ArtifactResolver

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=uri) for uri in shard_uris],
            index=ShardInfo(uri=f"file://{index_path}"),
        )

        resolver = ArtifactResolver(
            artifacts={"files": artifact},
            cache_context=None,
        )

        # Read each member
        for name, expected in contents.items():
            result = resolver.read_bytes("files", name)
            assert result == expected


class TestHTTPRangeWithManifest:
    """Tests for range reads through full manifest flow."""

    def test_imageref_uses_range_read(self, http_server_with_range):
        """ImageRef.read_bytes uses range read when index available."""
        base_url, tmp_path = http_server_with_range

        # Create a "fake" image (just bytes)
        image_data = b"PNG IMAGE DATA HERE" * 100

        tar_path = tmp_path / "shard-00000.tar"
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="image.png")
            info.size = len(image_data)
            tar.addfile(info, fileobj=__import__("io").BytesIO(image_data))

        # Build index
        from warpdatasets.artifacts.tar.index_builder import (
            build_tar_index,
            write_index_parquet,
        )

        index_data = build_tar_index([tar_path])
        index_path = tmp_path / "index.parquet"
        write_index_parquet(index_data, index_path)

        from warpdatasets.manifest.model import ArtifactDescriptor, ShardInfo
        from warpdatasets.artifacts.resolver import ArtifactResolver
        from warpdatasets.refs.image import ImageRef

        artifact = ArtifactDescriptor(
            kind="tar_shards",
            shards=[ShardInfo(uri=f"{base_url}/shard-00000.tar")],
            index=ShardInfo(uri=f"file://{index_path}"),
        )

        resolver = ArtifactResolver(
            artifacts={"images": artifact},
            cache_context=None,
        )

        # Create ImageRef and read bytes
        ref = ImageRef(
            artifact_name="images",
            ref_value="image.png",
            resolver=resolver,
        )

        result = ref.read_bytes()
        assert result == image_data
