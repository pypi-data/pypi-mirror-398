"""Tests for shard resolution and assignment.

These tests enforce invariant I2.2: Sharding is deterministic and non-overlapping.
"""

import os
import pytest

from warpdatasets.streaming.shard import (
    resolve_shard,
    assign_shards,
    ShardConfig,
)


class TestResolveShardNone:
    """Tests for shard=None behavior."""

    def test_shard_none_returns_none(self):
        """shard=None returns None (all shards)."""
        result = resolve_shard(None)
        assert result is None

    def test_shard_none_assign_returns_all(self):
        """When shard config is None, all URIs are returned."""
        uris = ["s3://bucket/part-0.parquet", "s3://bucket/part-1.parquet"]
        assigned = assign_shards(uris, None)
        assert assigned == uris


class TestResolveShardTuple:
    """Tests for explicit shard=(rank, world_size) behavior."""

    def test_shard_tuple_valid(self):
        """Valid (rank, world) tuple is accepted."""
        result = resolve_shard((0, 4))
        assert result == ShardConfig(rank=0, world_size=4)

    def test_shard_tuple_round_robin_assignment(self):
        """Round-robin assignment across ranks."""
        uris = [f"s3://bucket/part-{i}.parquet" for i in range(10)]

        # world_size=3
        rank0 = assign_shards(uris, ShardConfig(0, 3))
        rank1 = assign_shards(uris, ShardConfig(1, 3))
        rank2 = assign_shards(uris, ShardConfig(2, 3))

        # rank0 gets indices 0, 3, 6, 9
        assert rank0 == [uris[0], uris[3], uris[6], uris[9]]
        # rank1 gets indices 1, 4, 7
        assert rank1 == [uris[1], uris[4], uris[7]]
        # rank2 gets indices 2, 5, 8
        assert rank2 == [uris[2], uris[5], uris[8]]

    def test_shard_no_overlap(self):
        """Different ranks get non-overlapping shards."""
        uris = [f"s3://bucket/part-{i}.parquet" for i in range(20)]

        assigned_sets = []
        for rank in range(4):
            assigned = assign_shards(uris, ShardConfig(rank, 4))
            assigned_sets.append(set(assigned))

        # Check no overlap
        for i in range(4):
            for j in range(i + 1, 4):
                assert assigned_sets[i].isdisjoint(assigned_sets[j]), \
                    f"Rank {i} and {j} have overlapping shards"

    def test_shard_full_coverage(self):
        """Union of all ranks covers all shards."""
        uris = [f"s3://bucket/part-{i}.parquet" for i in range(17)]

        all_assigned = set()
        for rank in range(5):
            assigned = assign_shards(uris, ShardConfig(rank, 5))
            all_assigned.update(assigned)

        assert all_assigned == set(uris)

    def test_shard_single_worker(self):
        """world_size=1 returns all shards."""
        uris = [f"s3://bucket/part-{i}.parquet" for i in range(5)]
        assigned = assign_shards(uris, ShardConfig(0, 1))
        assert assigned == uris

    def test_shard_more_workers_than_shards(self):
        """Works when world_size > number of shards."""
        uris = ["s3://bucket/part-0.parquet", "s3://bucket/part-1.parquet"]

        rank0 = assign_shards(uris, ShardConfig(0, 5))
        rank1 = assign_shards(uris, ShardConfig(1, 5))
        rank2 = assign_shards(uris, ShardConfig(2, 5))
        rank3 = assign_shards(uris, ShardConfig(3, 5))
        rank4 = assign_shards(uris, ShardConfig(4, 5))

        # rank0 gets shard 0, rank1 gets shard 1, others get nothing
        assert rank0 == [uris[0]]
        assert rank1 == [uris[1]]
        assert rank2 == []
        assert rank3 == []
        assert rank4 == []

    def test_invalid_rank_negative_raises(self):
        """Negative rank raises ValueError."""
        with pytest.raises(ValueError, match="rank"):
            resolve_shard((-1, 4))

    def test_invalid_rank_too_large_raises(self):
        """rank >= world_size raises ValueError."""
        with pytest.raises(ValueError, match="rank"):
            resolve_shard((4, 4))

    def test_invalid_world_size_zero_raises(self):
        """world_size=0 raises ValueError."""
        with pytest.raises(ValueError, match="world_size"):
            resolve_shard((0, 0))

    def test_invalid_world_size_negative_raises(self):
        """Negative world_size raises ValueError."""
        with pytest.raises(ValueError, match="world_size"):
            resolve_shard((0, -1))


class TestResolveShardAuto:
    """Tests for shard='auto' environment variable parsing."""

    def test_shard_auto_from_env_rank_world(self, monkeypatch):
        """shard='auto' parses RANK and WORLD_SIZE."""
        monkeypatch.setenv("RANK", "2")
        monkeypatch.setenv("WORLD_SIZE", "8")

        result = resolve_shard("auto")
        assert result == ShardConfig(rank=2, world_size=8)

    def test_shard_auto_from_local_rank(self, monkeypatch):
        """Falls back to LOCAL_RANK and LOCAL_WORLD_SIZE."""
        monkeypatch.delenv("RANK", raising=False)
        monkeypatch.delenv("WORLD_SIZE", raising=False)
        monkeypatch.setenv("LOCAL_RANK", "1")
        monkeypatch.setenv("LOCAL_WORLD_SIZE", "4")

        result = resolve_shard("auto")
        assert result == ShardConfig(rank=1, world_size=4)

    def test_shard_auto_prefers_global_over_local(self, monkeypatch):
        """RANK/WORLD_SIZE takes precedence over LOCAL_RANK/LOCAL_WORLD_SIZE."""
        monkeypatch.setenv("RANK", "3")
        monkeypatch.setenv("WORLD_SIZE", "16")
        monkeypatch.setenv("LOCAL_RANK", "0")
        monkeypatch.setenv("LOCAL_WORLD_SIZE", "2")

        result = resolve_shard("auto")
        assert result == ShardConfig(rank=3, world_size=16)

    def test_shard_auto_missing_env_returns_none(self, monkeypatch):
        """Missing env vars returns None (single worker)."""
        monkeypatch.delenv("RANK", raising=False)
        monkeypatch.delenv("WORLD_SIZE", raising=False)
        monkeypatch.delenv("LOCAL_RANK", raising=False)
        monkeypatch.delenv("LOCAL_WORLD_SIZE", raising=False)

        result = resolve_shard("auto")
        assert result is None

    def test_shard_auto_partial_env_returns_none(self, monkeypatch):
        """Partial env vars (only RANK, no WORLD_SIZE) returns None."""
        monkeypatch.setenv("RANK", "0")
        monkeypatch.delenv("WORLD_SIZE", raising=False)

        result = resolve_shard("auto")
        assert result is None

    def test_shard_auto_invalid_env_returns_none(self, monkeypatch):
        """Invalid env var values return None (graceful fallback)."""
        monkeypatch.setenv("RANK", "not_a_number")
        monkeypatch.setenv("WORLD_SIZE", "8")

        result = resolve_shard("auto")
        assert result is None


class TestShardDeterminism:
    """Tests for deterministic sharding across runs."""

    def test_shard_assignment_is_deterministic(self):
        """Same inputs always produce same shard assignment."""
        uris = [f"s3://bucket/part-{i}.parquet" for i in range(100)]
        config = ShardConfig(rank=3, world_size=7)

        # Run multiple times
        results = [assign_shards(uris, config) for _ in range(10)]

        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

    def test_shard_assignment_independent_of_uri_order(self):
        """Shard assignment respects URI order (index-based)."""
        # Note: This tests that assignment is based on index, not content
        uris_a = ["s3://bucket/part-0.parquet", "s3://bucket/part-1.parquet"]
        uris_b = ["s3://bucket/part-1.parquet", "s3://bucket/part-0.parquet"]

        config = ShardConfig(rank=0, world_size=2)

        assigned_a = assign_shards(uris_a, config)
        assigned_b = assign_shards(uris_b, config)

        # rank 0 always gets index 0
        assert assigned_a == [uris_a[0]]
        assert assigned_b == [uris_b[0]]
