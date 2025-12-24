"""Tests for publish plan target URI generation.

Tests that target URIs are deterministic and follow the layout contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestPublishPlanPaths:
    """Tests for target URI generation in publish plans."""

    def test_table_shard_uris_follow_layout(self, tmp_path: Path):
        """Table shard URIs follow the expected layout."""
        import re
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create shards
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        for i in range(3):
            table = pa.table({"id": [i]})
            pq.write_table(table, data_dir / f"shard-{i:05d}.parquet")

        builder = ManifestBuilder(
            dataset_id="workspace/dataset",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        # Check shard URIs follow layout pattern
        version = plan.version
        for i, upload in enumerate(plan.table_uploads):
            expected_pattern = f"s3://bucket/warp/data/workspace/dataset/{version}/tables/main/shard-{i:05d}.parquet"
            assert upload.target_uri == expected_pattern
            # Also verify the URI format matches general pattern
            assert re.match(
                r"s3://bucket/warp/data/workspace/dataset/[a-f0-9]+/tables/main/shard-\d+\.parquet",
                upload.target_uri
            )

    def test_artifact_shard_uris_follow_layout(self, tmp_path: Path):
        """Artifact shard URIs follow the expected layout."""
        import re
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

        tar_shards = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "tar_out",
            shard_size_bytes=10 * 1024 * 1024,
        )

        builder = ManifestBuilder(
            dataset_id="workspace/dataset",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        builder.add_artifact("images", tar_shards)
        plan = builder.build_plan()

        # Check artifact URIs follow layout pattern
        version = plan.version
        for i, upload in enumerate(plan.artifact_uploads):
            expected_pattern = f"s3://bucket/warp/data/workspace/dataset/{version}/artifacts/images/shard-{i:05d}.tar"
            assert upload.target_uri == expected_pattern
            # Also verify the URI format matches general pattern
            assert re.match(
                r"s3://bucket/warp/data/workspace/dataset/[a-f0-9]+/artifacts/images/shard-\d+\.tar",
                upload.target_uri
            )

    def test_manifest_uri_follows_layout(self, tmp_path: Path):
        """Manifest URI follows the expected layout."""
        import re
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder(
            dataset_id="workspace/dataset",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        version = plan.version
        expected = f"s3://bucket/warp/manifests/workspace/dataset/{version}.json"
        assert plan.manifest_uri == expected
        # Also verify format pattern
        assert re.match(
            r"s3://bucket/warp/manifests/workspace/dataset/[a-f0-9]+\.json",
            plan.manifest_uri
        )

    def test_latest_pointer_uri_follows_layout(self, tmp_path: Path):
        """Latest pointer URI follows the expected layout."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder(
            dataset_id="workspace/dataset",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        expected = "s3://bucket/warp/manifests/workspace/dataset/latest.json"
        assert plan.latest_uri == expected


class TestShardNumbering:
    """Tests for deterministic shard numbering."""

    def test_table_shards_numbered_sequentially(self, tmp_path: Path):
        """Table shards are numbered 0, 1, 2, ..."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        for i in range(5):
            table = pa.table({"id": [i]})
            pq.write_table(table, data_dir / f"part_{i}.parquet")

        builder = ManifestBuilder(
            dataset_id="test/ds",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        # Check numbering
        for i, upload in enumerate(plan.table_uploads):
            assert f"shard-{i:05d}.parquet" in upload.target_uri

    def test_shard_order_stable_regardless_of_input_names(self, tmp_path: Path):
        """Shard numbering is stable regardless of input file names."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create files with random names
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        names = ["zebra.parquet", "apple.parquet", "mango.parquet"]
        for i, name in enumerate(names):
            table = pa.table({"id": [i], "name": [name]})
            pq.write_table(table, data_dir / name)

        builder = ManifestBuilder(
            dataset_id="test/ds",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        # Shards should be in sorted order by original filename
        sorted_names = sorted(names)
        for i, upload in enumerate(plan.table_uploads):
            # The source should correspond to sorted name
            assert sorted_names[i] in str(upload.source_path)


class TestPlanSummary:
    """Tests for publish plan summary statistics."""

    def test_plan_has_total_bytes(self, tmp_path: Path):
        """Publish plan includes total bytes to upload."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": list(range(1000))})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder(
            dataset_id="test/ds",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        plan = builder.build_plan()

        assert plan.total_bytes > 0
        assert plan.shard_count >= 1

    def test_plan_has_shard_counts(self, tmp_path: Path):
        """Publish plan includes shard counts."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.packer import pack_directory_to_tar_shards

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        for i in range(3):
            table = pa.table({"id": [i]})
            pq.write_table(table, data_dir / f"shard-{i:05d}.parquet")

        artifact_dir = tmp_path / "artifacts"
        artifact_dir.mkdir()
        (artifact_dir / "test.txt").write_bytes(b"test")

        tar_shards = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "tar_out",
            shard_size_bytes=10 * 1024 * 1024,
        )

        builder = ManifestBuilder(
            dataset_id="test/ds",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        builder.add_artifact("raw", tar_shards)
        plan = builder.build_plan()

        assert plan.table_shard_count == 3
        assert plan.artifact_shard_count == 1
        assert plan.shard_count == 4
