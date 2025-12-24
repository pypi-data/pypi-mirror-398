"""Tests for prefetch planner.

Tests Phase 4 invariant I4.5: Prefetch respects sharding.
"""

from __future__ import annotations

import pytest


class TestPrefetchPlanner:
    """Tests for shard-aware prefetch planning."""

    def test_plan_next_shards_from_current(self):
        """Planner returns next N shards from current position."""
        from warpdatasets.prefetch.planners import TableShardPlanner

        shards = [f"s3://bucket/shard-{i}.parquet" for i in range(10)]
        planner = TableShardPlanner(shards, ahead=3)

        # At shard 0, should plan shards 1, 2, 3
        next_shards = planner.get_next_shards(current_index=0)
        assert len(next_shards) == 3
        assert next_shards == shards[1:4]

    def test_plan_respects_ahead_limit(self):
        """Planner respects ahead limit."""
        from warpdatasets.prefetch.planners import TableShardPlanner

        shards = [f"s3://bucket/shard-{i}.parquet" for i in range(20)]
        planner = TableShardPlanner(shards, ahead=5)

        next_shards = planner.get_next_shards(current_index=0)
        assert len(next_shards) == 5

    def test_plan_at_end_returns_fewer(self):
        """Planner returns fewer shards near end of list."""
        from warpdatasets.prefetch.planners import TableShardPlanner

        shards = [f"s3://bucket/shard-{i}.parquet" for i in range(5)]
        planner = TableShardPlanner(shards, ahead=3)

        # At shard 3, only shard 4 remains
        next_shards = planner.get_next_shards(current_index=3)
        assert len(next_shards) == 1
        assert next_shards == [shards[4]]

    def test_plan_at_last_shard_returns_empty(self):
        """Planner returns empty list at last shard."""
        from warpdatasets.prefetch.planners import TableShardPlanner

        shards = [f"s3://bucket/shard-{i}.parquet" for i in range(5)]
        planner = TableShardPlanner(shards, ahead=3)

        next_shards = planner.get_next_shards(current_index=4)
        assert next_shards == []


class TestShardAwarePrefetch:
    """Tests for sharding-aware prefetch."""

    def test_respects_worker_assignment(self):
        """Planner only suggests shards assigned to this worker."""
        from warpdatasets.prefetch.planners import TableShardPlanner
        from warpdatasets.streaming.shard import assign_shards, ShardConfig

        all_shards = [f"s3://bucket/shard-{i}.parquet" for i in range(10)]

        # Worker 0 of 2 gets shards 0, 2, 4, 6, 8
        config = ShardConfig(rank=0, world_size=2)
        worker_shards = assign_shards(all_shards, config)

        planner = TableShardPlanner(worker_shards, ahead=2)

        # At shard 0 (index 0), next should be shards 2, 4 (indices 1, 2)
        next_shards = planner.get_next_shards(current_index=0)
        assert len(next_shards) == 2
        assert next_shards == [worker_shards[1], worker_shards[2]]

    def test_different_workers_different_plans(self):
        """Different workers have non-overlapping prefetch plans."""
        from warpdatasets.prefetch.planners import TableShardPlanner
        from warpdatasets.streaming.shard import assign_shards, ShardConfig

        all_shards = [f"s3://bucket/shard-{i}.parquet" for i in range(10)]

        # Worker 0 shards
        config0 = ShardConfig(rank=0, world_size=2)
        worker0_shards = assign_shards(all_shards, config0)
        planner0 = TableShardPlanner(worker0_shards, ahead=2)

        # Worker 1 shards
        config1 = ShardConfig(rank=1, world_size=2)
        worker1_shards = assign_shards(all_shards, config1)
        planner1 = TableShardPlanner(worker1_shards, ahead=2)

        # Plans should be disjoint
        plan0 = planner0.get_next_shards(current_index=0)
        plan1 = planner1.get_next_shards(current_index=0)

        assert set(plan0).isdisjoint(set(plan1))


class TestPrefetchWithCachedShards:
    """Tests for prefetch planning with cache awareness."""

    def test_skips_already_cached(self):
        """Planner skips shards already in cache."""
        from warpdatasets.prefetch.planners import TableShardPlanner

        shards = [f"s3://bucket/shard-{i}.parquet" for i in range(10)]

        # Shards 1 and 2 are cached
        cached_keys = {
            f"s3://bucket/shard-1.parquet": True,
            f"s3://bucket/shard-2.parquet": True,
        }

        def is_cached(uri):
            return uri in cached_keys

        planner = TableShardPlanner(shards, ahead=4, is_cached_fn=is_cached)

        # At shard 0, should skip 1, 2 and return 3, 4, 5, 6
        next_shards = planner.get_next_shards(current_index=0)

        assert "s3://bucket/shard-1.parquet" not in next_shards
        assert "s3://bucket/shard-2.parquet" not in next_shards
        assert "s3://bucket/shard-3.parquet" in next_shards

    def test_fills_ahead_count_skipping_cached(self):
        """Planner fills ahead count by looking further when some cached."""
        from warpdatasets.prefetch.planners import TableShardPlanner

        shards = [f"s3://bucket/shard-{i}.parquet" for i in range(10)]

        # Shard 1 is cached
        cached_keys = {f"s3://bucket/shard-1.parquet": True}

        def is_cached(uri):
            return uri in cached_keys

        planner = TableShardPlanner(shards, ahead=2, is_cached_fn=is_cached)

        # At shard 0, should return shards 2, 3 (skipping cached 1)
        next_shards = planner.get_next_shards(current_index=0)

        assert len(next_shards) == 2
        assert shards[1] not in next_shards
        assert shards[2] in next_shards
        assert shards[3] in next_shards
