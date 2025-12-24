"""Shard resolution and assignment for distributed training.

Provides deterministic, non-overlapping shard assignment at the
parquet file level for distributed/multi-worker training.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ShardConfig:
    """Configuration for shard assignment.

    Attributes:
        rank: Worker rank (0-indexed)
        world_size: Total number of workers
    """

    rank: int
    world_size: int

    def __post_init__(self):
        if self.world_size <= 0:
            raise ValueError(f"world_size must be positive, got {self.world_size}")
        if self.rank < 0 or self.rank >= self.world_size:
            raise ValueError(
                f"rank must be in [0, world_size), got rank={self.rank}, world_size={self.world_size}"
            )


def resolve_shard(
    shard: tuple[int, int] | str | None,
) -> ShardConfig | None:
    """Resolve shard specification to ShardConfig.

    Args:
        shard: One of:
            - None: No sharding (all shards)
            - (rank, world_size): Explicit sharding
            - "auto": Parse from environment variables

    Returns:
        ShardConfig if sharding is configured, None otherwise

    Raises:
        ValueError: If explicit (rank, world_size) is invalid
    """
    if shard is None:
        return None

    if isinstance(shard, str):
        if shard == "auto":
            return _resolve_shard_auto()
        raise ValueError(f"Unknown shard string: {shard!r}. Use 'auto' or (rank, world_size)")

    if isinstance(shard, tuple) and len(shard) == 2:
        rank, world_size = shard
        return ShardConfig(rank=rank, world_size=world_size)

    raise ValueError(f"Invalid shard specification: {shard!r}")


def _resolve_shard_auto() -> ShardConfig | None:
    """Parse shard configuration from environment variables.

    Checks in order:
    1. RANK + WORLD_SIZE (standard distributed)
    2. LOCAL_RANK + LOCAL_WORLD_SIZE (local parallelism)

    Returns:
        ShardConfig if env vars found and valid, None otherwise
    """
    # Try global RANK/WORLD_SIZE first
    rank_str = os.environ.get("RANK")
    world_str = os.environ.get("WORLD_SIZE")

    if rank_str is not None and world_str is not None:
        try:
            rank = int(rank_str)
            world_size = int(world_str)
            return ShardConfig(rank=rank, world_size=world_size)
        except (ValueError, TypeError):
            pass  # Fall through to try local

    # Try LOCAL_RANK/LOCAL_WORLD_SIZE
    rank_str = os.environ.get("LOCAL_RANK")
    world_str = os.environ.get("LOCAL_WORLD_SIZE")

    if rank_str is not None and world_str is not None:
        try:
            rank = int(rank_str)
            world_size = int(world_str)
            return ShardConfig(rank=rank, world_size=world_size)
        except (ValueError, TypeError):
            pass

    # No valid env vars found
    return None


def assign_shards(
    uris: Sequence[str],
    config: ShardConfig | None,
) -> list[str]:
    """Assign shards to a worker based on config.

    Uses round-robin assignment at the file level:
    - Worker 0 gets indices 0, world_size, 2*world_size, ...
    - Worker 1 gets indices 1, world_size+1, 2*world_size+1, ...

    Args:
        uris: List of shard URIs
        config: Shard configuration, or None for all shards

    Returns:
        List of URIs assigned to this worker
    """
    if config is None:
        return list(uris)

    # Round-robin assignment: rank gets indices [rank, rank+world, rank+2*world, ...]
    return [uris[i] for i in range(config.rank, len(uris), config.world_size)]
