"""Tests for publish manifest determinism.

Tests Phase 5 invariant I5.3: Dataset identity remains deterministic.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestManifestDeterminism:
    """Tests that same inputs produce same manifest."""

    def test_same_inputs_same_version_hash(self, tmp_path: Path):
        """Same inputs produce same manifest and version hash."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create parquet shard
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        table = pa.table({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        # Build manifest twice
        builder1 = ManifestBuilder(
            dataset_id="test/dataset",
            base_uri="s3://bucket/warp",
        )
        builder1.add_table("main", list(data_dir.glob("*.parquet")))
        manifest1 = builder1.build()

        builder2 = ManifestBuilder(
            dataset_id="test/dataset",
            base_uri="s3://bucket/warp",
        )
        builder2.add_table("main", list(data_dir.glob("*.parquet")))
        manifest2 = builder2.build()

        # Version hashes should match
        assert manifest1.version_hash == manifest2.version_hash

    def test_file_order_does_not_affect_hash(self, tmp_path: Path):
        """Ordering of input files does not change result."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create multiple parquet shards
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        for i in range(3):
            table = pa.table({"id": [i], "value": [i * 10]})
            pq.write_table(table, data_dir / f"shard-{i:05d}.parquet")

        # Get files in different orders
        files = list(data_dir.glob("*.parquet"))
        files_reversed = list(reversed(files))

        # Build with forward order
        builder1 = ManifestBuilder(
            dataset_id="test/dataset",
            base_uri="s3://bucket/warp",
        )
        builder1.add_table("main", files)
        manifest1 = builder1.build()

        # Build with reverse order
        builder2 = ManifestBuilder(
            dataset_id="test/dataset",
            base_uri="s3://bucket/warp",
        )
        builder2.add_table("main", files_reversed)
        manifest2 = builder2.build()

        # Version hashes should match (order normalized internally)
        assert manifest1.version_hash == manifest2.version_hash

    def test_different_data_produces_different_hash(self, tmp_path: Path):
        """Different data produces different version hash."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create first dataset
        data_dir1 = tmp_path / "data1"
        data_dir1.mkdir()
        table1 = pa.table({"id": [1, 2, 3]})
        pq.write_table(table1, data_dir1 / "shard-00000.parquet")

        # Create second dataset with different data
        data_dir2 = tmp_path / "data2"
        data_dir2.mkdir()
        table2 = pa.table({"id": [4, 5, 6]})
        pq.write_table(table2, data_dir2 / "shard-00000.parquet")

        builder1 = ManifestBuilder("test/dataset", "s3://bucket/warp")
        builder1.add_table("main", list(data_dir1.glob("*.parquet")))
        manifest1 = builder1.build()

        builder2 = ManifestBuilder("test/dataset", "s3://bucket/warp")
        builder2.add_table("main", list(data_dir2.glob("*.parquet")))
        manifest2 = builder2.build()

        # Different data should produce different hash
        assert manifest1.version_hash != manifest2.version_hash


class TestArtifactPackingDeterminism:
    """Tests that artifact packing is deterministic."""

    def test_artifact_packing_order_stable(self, tmp_path: Path):
        """Artifact packing produces stable ordering."""
        from warpdatasets.publish.packer import pack_directory_to_tar_shards

        # Create files in random order
        artifact_dir = tmp_path / "artifacts"
        artifact_dir.mkdir()

        for name in ["zebra.jpg", "apple.jpg", "mango.jpg"]:
            (artifact_dir / name).write_bytes(b"test data for " + name.encode())

        # Pack twice
        shards1 = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "out1",
            shard_size_bytes=10 * 1024 * 1024,  # 10MB
        )

        shards2 = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "out2",
            shard_size_bytes=10 * 1024 * 1024,
        )

        # Member lists should match
        assert len(shards1) == len(shards2)
        for s1, s2 in zip(shards1, shards2):
            assert s1.members == s2.members

    def test_tar_content_is_reproducible(self, tmp_path: Path):
        """Tar file content is byte-for-byte reproducible."""
        from warpdatasets.publish.packer import pack_directory_to_tar_shards

        # Create test files
        artifact_dir = tmp_path / "artifacts"
        artifact_dir.mkdir()
        (artifact_dir / "test.txt").write_text("hello world")

        # Pack twice to different outputs
        shards1 = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "out1",
            shard_size_bytes=10 * 1024 * 1024,
        )

        shards2 = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "out2",
            shard_size_bytes=10 * 1024 * 1024,
        )

        # Tar files should be identical
        assert len(shards1) == len(shards2) == 1
        content1 = shards1[0].path.read_bytes()
        content2 = shards2[0].path.read_bytes()
        assert content1 == content2


class TestNoLocalPathsInManifest:
    """Tests that published manifests have no local paths."""

    def test_manifest_has_no_file_uris(self, tmp_path: Path):
        """Published manifest contains no file:// URIs."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder

        # Create parquet shard
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1, 2, 3]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        builder = ManifestBuilder(
            dataset_id="test/dataset",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        manifest = builder.build()

        # Check all URIs
        for table_name, table_desc in manifest.tables.items():
            for shard in table_desc.shards:
                assert not shard.uri.startswith("file://"), f"Local path found: {shard.uri}"
                assert not shard.uri.startswith("/"), f"Absolute path found: {shard.uri}"

    def test_manifest_has_no_absolute_paths(self, tmp_path: Path):
        """Published manifest contains no absolute local paths."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.publish.builder import ManifestBuilder
        from warpdatasets.publish.packer import pack_directory_to_tar_shards

        # Create parquet shard
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        table = pa.table({"id": [1], "image": ["img001.jpg"]})
        pq.write_table(table, data_dir / "shard-00000.parquet")

        # Create artifact
        artifact_dir = tmp_path / "artifacts"
        artifact_dir.mkdir()
        (artifact_dir / "img001.jpg").write_bytes(b"fake image")

        tar_shards = pack_directory_to_tar_shards(
            artifact_dir,
            output_dir=tmp_path / "tar_out",
            shard_size_bytes=10 * 1024 * 1024,
        )

        builder = ManifestBuilder(
            dataset_id="test/dataset",
            base_uri="s3://bucket/warp",
        )
        builder.add_table("main", list(data_dir.glob("*.parquet")))
        builder.add_artifact("images", tar_shards)
        builder.add_binding("main", "image", "images", "image", "tar_member_path")
        manifest = builder.build()

        # Convert to dict and check all values
        manifest_dict = manifest.to_dict()
        import json
        manifest_json = json.dumps(manifest_dict)

        assert "file://" not in manifest_json
        # Check no tmp_path leaks
        assert str(tmp_path) not in manifest_json
