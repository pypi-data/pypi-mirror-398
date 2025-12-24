"""Tests for manifest canonicalization and version hashing.

These tests enforce invariant I1.3: Deterministic version identity.
"""

import pytest

from warpdatasets.manifest.canon import canonical_json, compute_version_hash
from warpdatasets.manifest.model import Manifest, TableDescriptor, ShardInfo


class TestCanonicalJson:
    """Tests for canonical JSON serialization."""

    def test_canonical_json_stable_key_order(self):
        """Same dict with different key order produces identical bytes."""
        dict_a = {"z": 1, "a": 2, "m": 3}
        dict_b = {"a": 2, "m": 3, "z": 1}
        dict_c = {"m": 3, "z": 1, "a": 2}

        result_a = canonical_json(dict_a)
        result_b = canonical_json(dict_b)
        result_c = canonical_json(dict_c)

        assert result_a == result_b == result_c
        # Keys should be sorted in output
        assert b'"a":2' in result_a
        assert result_a.index(b'"a"') < result_a.index(b'"m"') < result_a.index(b'"z"')

    def test_canonical_json_nested_key_order(self):
        """Nested dicts also have stable key ordering."""
        nested_a = {"outer": {"z": 1, "a": 2}, "inner": {"b": 3, "c": 4}}
        nested_b = {"inner": {"c": 4, "b": 3}, "outer": {"a": 2, "z": 1}}

        assert canonical_json(nested_a) == canonical_json(nested_b)

    def test_canonical_json_list_order_preserved(self):
        """Lists preserve their order (not sorted)."""
        list_a = {"items": [3, 1, 2]}
        list_b = {"items": [1, 2, 3]}

        # Lists should NOT be equal - order matters
        assert canonical_json(list_a) != canonical_json(list_b)

    def test_canonical_json_no_whitespace(self):
        """Output has no unnecessary whitespace."""
        data = {"key": "value", "nested": {"a": 1}}
        result = canonical_json(data)

        assert b" " not in result
        assert b"\n" not in result
        assert b"\t" not in result

    def test_canonical_json_utf8_encoding(self):
        """Output is valid UTF-8."""
        data = {"unicode": "hello world", "emoji": "test"}
        result = canonical_json(data)

        # Should be decodable as UTF-8
        decoded = result.decode("utf-8")
        assert "hello world" in decoded

    def test_canonical_json_integer_normalization(self):
        """Integers are serialized consistently."""
        data = {"count": 42, "zero": 0, "negative": -10}
        result = canonical_json(data)

        assert b"42" in result
        assert b"0" in result
        assert b"-10" in result

    def test_canonical_json_float_normalization(self):
        """Floats are serialized consistently."""
        data = {"pi": 3.14159, "small": 0.001}
        result = canonical_json(data)

        # Should serialize without trailing zeros or scientific notation issues
        decoded = result.decode("utf-8")
        assert "3.14159" in decoded

    def test_canonical_json_rejects_nan(self):
        """NaN values should raise an error."""
        import math

        data = {"bad": math.nan}
        with pytest.raises(ValueError, match="[Nn]aN|not.*JSON"):
            canonical_json(data)

    def test_canonical_json_rejects_infinity(self):
        """Infinity values should raise an error."""
        import math

        data = {"bad": math.inf}
        with pytest.raises(ValueError, match="[Ii]nfinity|not.*JSON"):
            canonical_json(data)

    def test_canonical_json_bool_values(self):
        """Booleans serialize as lowercase true/false."""
        data = {"enabled": True, "disabled": False}
        result = canonical_json(data)

        assert b"true" in result
        assert b"false" in result
        assert b"True" not in result
        assert b"False" not in result

    def test_canonical_json_null_values(self):
        """None serializes as null."""
        data = {"empty": None}
        result = canonical_json(data)

        assert b"null" in result
        assert b"None" not in result


class TestVersionHash:
    """Tests for deterministic version hashing."""

    def test_version_hash_deterministic(self):
        """Same manifest always produces same hash."""
        manifest_data = {
            "dataset": "test/example",
            "tables": {
                "main": {
                    "format": "parquet",
                    "uris": ["s3://bucket/data/part-0000.parquet"],
                }
            },
        }

        hash1 = compute_version_hash(manifest_data)
        hash2 = compute_version_hash(manifest_data)
        hash3 = compute_version_hash(manifest_data)

        assert hash1 == hash2 == hash3

    def test_version_hash_key_order_independent(self):
        """Key order doesn't affect hash."""
        manifest_a = {
            "dataset": "test/example",
            "tables": {"main": {"format": "parquet", "uris": []}},
        }
        manifest_b = {
            "tables": {"main": {"uris": [], "format": "parquet"}},
            "dataset": "test/example",
        }

        assert compute_version_hash(manifest_a) == compute_version_hash(manifest_b)

    def test_version_hash_changes_on_semantic_change(self):
        """Adding/removing URIs changes the hash."""
        manifest_base = {
            "dataset": "test/example",
            "tables": {
                "main": {
                    "format": "parquet",
                    "uris": ["s3://bucket/data/part-0000.parquet"],
                }
            },
        }
        manifest_with_extra_uri = {
            "dataset": "test/example",
            "tables": {
                "main": {
                    "format": "parquet",
                    "uris": [
                        "s3://bucket/data/part-0000.parquet",
                        "s3://bucket/data/part-0001.parquet",
                    ],
                }
            },
        }

        hash_base = compute_version_hash(manifest_base)
        hash_extra = compute_version_hash(manifest_with_extra_uri)

        assert hash_base != hash_extra

    def test_version_hash_changes_on_dataset_name_change(self):
        """Changing dataset name changes hash."""
        manifest_a = {
            "dataset": "workspace/name_a",
            "tables": {"main": {"format": "parquet", "uris": []}},
        }
        manifest_b = {
            "dataset": "workspace/name_b",
            "tables": {"main": {"format": "parquet", "uris": []}},
        }

        assert compute_version_hash(manifest_a) != compute_version_hash(manifest_b)

    def test_version_hash_is_hex_string(self):
        """Hash is a valid hex string of expected length."""
        manifest_data = {
            "dataset": "test/example",
            "tables": {"main": {"format": "parquet", "uris": []}},
        }

        version_hash = compute_version_hash(manifest_data)

        # Should be 16 hex chars (first 16 of sha256)
        assert len(version_hash) == 16
        assert all(c in "0123456789abcdef" for c in version_hash)

    def test_non_hashed_metadata_does_not_change_hash(self):
        """Fields in 'meta' envelope don't affect version hash."""
        manifest_without_meta = {
            "dataset": "test/example",
            "tables": {"main": {"format": "parquet", "uris": []}},
        }
        manifest_with_meta = {
            "dataset": "test/example",
            "tables": {"main": {"format": "parquet", "uris": []}},
            "meta": {
                "created_at": "2025-01-01T00:00:00Z",
                "author": "test-user",
            },
        }

        hash_without = compute_version_hash(manifest_without_meta)
        hash_with = compute_version_hash(manifest_with_meta)

        assert hash_without == hash_with


class TestManifestModel:
    """Tests for Manifest dataclass serialization."""

    def test_manifest_to_dict_canonical(self):
        """Manifest can be converted to canonical dict for hashing."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[
                        ShardInfo(uri="s3://bucket/part-0000.parquet"),
                        ShardInfo(uri="s3://bucket/part-0001.parquet"),
                    ],
                )
            },
        )

        # Should be convertible to dict for hashing
        manifest_dict = manifest.to_hashable_dict()
        version_hash = compute_version_hash(manifest_dict)

        assert len(version_hash) == 16

    def test_manifest_version_hash_property(self):
        """Manifest has a version_hash property that is deterministic."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/part-0000.parquet")],
                )
            },
        )

        hash1 = manifest.version_hash
        hash2 = manifest.version_hash

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_manifest_with_optional_fields(self):
        """Manifest with optional fields still produces consistent hash."""
        manifest_minimal = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/part-0000.parquet")],
                )
            },
        )

        manifest_with_schema = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/part-0000.parquet")],
                    schema={"id": "BIGINT", "name": "VARCHAR"},
                )
            },
        )

        # Different content = different hash
        assert manifest_minimal.version_hash != manifest_with_schema.version_hash

    def test_manifest_artifacts_placeholder(self):
        """Manifest supports artifacts field (placeholder for Phase 3)."""
        manifest = Manifest(
            dataset="test/example",
            tables={
                "main": TableDescriptor(
                    format="parquet",
                    shards=[ShardInfo(uri="s3://bucket/part-0000.parquet")],
                )
            },
            artifacts={},  # Empty but present
            bindings=[],
        )

        # Should work and produce a hash
        assert len(manifest.version_hash) == 16
