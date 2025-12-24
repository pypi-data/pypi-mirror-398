"""Tests for publish idempotency.

Tests Phase 5 invariant I5.2: Publish is idempotent.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestUploadIdempotency:
    """Tests that uploads are skipped when content already exists."""

    def test_skips_existing_shard_same_size(self, tmp_path: Path):
        """Skips upload if shard exists with same size."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.uploader import Uploader

        # Create shard
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1, 2, 3]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder("test/ds", "s3://bucket/warp")
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        # Mock storage that says file exists with correct size
        mock_storage = MagicMock()
        mock_storage.head_object.return_value = {
            "size": plan.table_uploads[0].source_path.stat().st_size
        }
        mock_storage.put_object = MagicMock()
        mock_storage.put_file = MagicMock()

        uploader = Uploader(storage=mock_storage)
        uploader.execute_plan(plan, skip_existing=True)

        # put_file should not be called for shards (they were skipped)
        # Check that put_file was never called (shards use put_file)
        assert mock_storage.put_file.call_count == 0

    def test_uploads_missing_shard(self, tmp_path: Path):
        """Uploads shard if it doesn't exist."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.uploader import Uploader

        # Create shard
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1, 2, 3]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder("test/ds", "s3://bucket/warp")
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        # Mock storage that says file doesn't exist
        mock_storage = MagicMock()
        mock_storage.head_object.return_value = None  # Not found
        mock_storage.put_object = MagicMock()

        uploader = Uploader(storage=mock_storage)
        uploader.execute_plan(plan, skip_existing=True)

        # put_file should be called for the shard (shards use put_file)
        assert mock_storage.put_file.call_count >= 1

    def test_uploads_shard_with_different_size(self, tmp_path: Path):
        """Uploads shard if remote size differs."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.uploader import Uploader

        # Create shard
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1, 2, 3]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder("test/ds", "s3://bucket/warp")
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        actual_size = plan.table_uploads[0].source_path.stat().st_size

        # Mock storage that says file exists but with different size
        mock_storage = MagicMock()
        mock_storage.head_object.return_value = {"size": actual_size + 100}
        mock_storage.put_object = MagicMock()

        uploader = Uploader(storage=mock_storage)
        uploader.execute_plan(plan, skip_existing=True)

        # put_file should be called because size differs (shards use put_file)
        assert mock_storage.put_file.call_count >= 1


class TestManifestIdempotency:
    """Tests that manifest upload is idempotent."""

    def test_always_uploads_manifest(self, tmp_path: Path):
        """Manifest is always uploaded (to ensure consistency)."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.uploader import Uploader

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder("test/ds", "s3://bucket/warp")
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        mock_storage = MagicMock()
        mock_storage.head_object.return_value = {"size": 100}  # Pretend shard exists
        mock_storage.put_object = MagicMock()

        uploader = Uploader(storage=mock_storage)
        uploader.execute_plan(plan, skip_existing=True)

        # Manifest should always be uploaded
        manifest_puts = [
            call for call in mock_storage.put_object.call_args_list
            if ".json" in str(call[0][0]) and "latest" not in str(call[0][0])
            if call[0]
        ]
        assert len(manifest_puts) == 1


class TestVersionHashIdempotency:
    """Tests that version hash is stable across republishes."""

    def test_same_content_same_hash_across_runs(self, tmp_path: Path):
        """Same content produces same hash even when rebuilt."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create data once
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        # Build plan multiple times
        hashes = []
        for _ in range(3):
            builder = ManifestBuilder("test/ds", "s3://bucket/warp")
            builder.add_table("main", list(data_dir.glob("*.parquet")))
            plan = builder.build_plan()
            hashes.append(plan.version)

        # All hashes should be identical
        assert len(set(hashes)) == 1

    def test_adding_artifact_changes_hash(self, tmp_path: Path):
        """Adding an artifact changes the version hash."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.packer import pack_directory_to_tar_shards

        # Create table
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1], "ref": ["a.jpg"]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        # Create artifact
        artifact_dir = tmp_path / "artifacts"
        artifact_dir.mkdir()
        (artifact_dir / "a.jpg").write_bytes(b"image")

        # Build without artifact
        builder1 = ManifestBuilder("test/ds", "s3://bucket/warp")
        builder1.add_table("main", list(data_dir.glob("*.parquet")))
        plan1 = builder1.build_plan()

        # Build with artifact
        tar_shards = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "tar_out",
            shard_size_bytes=10 * 1024 * 1024,
        )

        builder2 = ManifestBuilder("test/ds", "s3://bucket/warp")
        builder2.add_table("main", list(data_dir.glob("*.parquet")))
        builder2.add_artifact("images", tar_shards)
        plan2 = builder2.build_plan()

        # Hashes should differ
        assert plan1.version != plan2.version
