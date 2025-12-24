"""Artifact packer for creating tar shards.

Packs directories into deterministic tar archives.
"""

from __future__ import annotations

import os
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass
class TarShard:
    """A packed tar shard."""

    path: Path
    index: int
    members: list[str] = field(default_factory=list)
    size_bytes: int = 0

    @property
    def size(self) -> int:
        """Alias for size_bytes."""
        return self.size_bytes


def pack_directory_to_tar_shards(
    source_dir: Path,
    output_dir: Path,
    shard_size_bytes: int = 512 * 1024 * 1024,  # 512MB default
    shard_prefix: str = "shard",
) -> list[TarShard]:
    """Pack a directory into tar shards.

    Creates deterministic tar archives by:
    - Sorting files alphabetically
    - Using fixed mtime/uid/gid for reproducibility
    - Splitting at shard size boundaries

    Args:
        source_dir: Directory to pack
        output_dir: Directory for output tar files
        shard_size_bytes: Target size per shard
        shard_prefix: Prefix for shard filenames

    Returns:
        List of TarShard objects
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all files with stable ordering
    files = []
    for root, dirs, filenames in os.walk(source_dir):
        # Sort directories for stable traversal
        dirs.sort()
        for filename in sorted(filenames):
            file_path = Path(root) / filename
            if file_path.is_file():
                # Compute relative path for tar member name
                rel_path = file_path.relative_to(source_dir)
                files.append((str(rel_path), file_path))

    # Sort by relative path for determinism
    files.sort(key=lambda x: x[0])

    if not files:
        return []

    # Pack into shards
    shards = []
    current_shard_index = 0
    current_shard_size = 0
    current_members = []
    current_tar_path = None
    current_tar = None

    def start_new_shard():
        nonlocal current_shard_index, current_shard_size, current_members
        nonlocal current_tar_path, current_tar

        if current_tar is not None:
            current_tar.close()
            shards.append(TarShard(
                path=current_tar_path,
                index=len(shards),
                members=current_members,
                size_bytes=current_tar_path.stat().st_size,
            ))

        current_shard_index += 1
        current_shard_size = 0
        current_members = []
        current_tar_path = output_dir / f"{shard_prefix}-{len(shards):05d}.tar"
        current_tar = tarfile.open(current_tar_path, "w")

    def add_file_to_current(member_name: str, file_path: Path):
        nonlocal current_shard_size

        # Create TarInfo with deterministic metadata
        info = tarfile.TarInfo(name=member_name)
        info.size = file_path.stat().st_size
        info.mtime = 0  # Fixed mtime for reproducibility
        info.uid = 0
        info.gid = 0
        info.mode = 0o644

        with open(file_path, "rb") as f:
            current_tar.addfile(info, f)

        current_members.append(member_name)
        current_shard_size += info.size

    # Start first shard
    start_new_shard()

    for member_name, file_path in files:
        file_size = file_path.stat().st_size

        # Check if we need a new shard
        # (but always add at least one file per shard)
        if current_shard_size > 0 and current_shard_size + file_size > shard_size_bytes:
            start_new_shard()

        add_file_to_current(member_name, file_path)

    # Close final shard
    if current_tar is not None:
        current_tar.close()
        shards.append(TarShard(
            path=current_tar_path,
            index=len(shards),
            members=current_members,
            size_bytes=current_tar_path.stat().st_size,
        ))

    return shards


def pack_files_to_tar_shards(
    files: Sequence[tuple[str, Path]],
    output_dir: Path,
    shard_size_bytes: int = 512 * 1024 * 1024,
    shard_prefix: str = "shard",
) -> list[TarShard]:
    """Pack specific files into tar shards.

    Args:
        files: List of (member_name, file_path) tuples
        output_dir: Directory for output tar files
        shard_size_bytes: Target size per shard
        shard_prefix: Prefix for shard filenames

    Returns:
        List of TarShard objects
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sort for determinism
    sorted_files = sorted(files, key=lambda x: x[0])

    if not sorted_files:
        return []

    shards = []
    current_shard_size = 0
    current_members = []
    current_tar_path = output_dir / f"{shard_prefix}-{len(shards):05d}.tar"
    current_tar = tarfile.open(current_tar_path, "w")

    for member_name, file_path in sorted_files:
        file_size = file_path.stat().st_size

        # Check if we need a new shard
        if current_shard_size > 0 and current_shard_size + file_size > shard_size_bytes:
            current_tar.close()
            shards.append(TarShard(
                path=current_tar_path,
                index=len(shards),
                members=current_members,
                size_bytes=current_tar_path.stat().st_size,
            ))

            current_shard_size = 0
            current_members = []
            current_tar_path = output_dir / f"{shard_prefix}-{len(shards):05d}.tar"
            current_tar = tarfile.open(current_tar_path, "w")

        # Add file
        info = tarfile.TarInfo(name=member_name)
        info.size = file_size
        info.mtime = 0
        info.uid = 0
        info.gid = 0
        info.mode = 0o644

        with open(file_path, "rb") as f:
            current_tar.addfile(info, f)

        current_members.append(member_name)
        current_shard_size += file_size

    # Close final shard
    current_tar.close()
    if current_members:
        shards.append(TarShard(
            path=current_tar_path,
            index=len(shards),
            members=current_members,
            size_bytes=current_tar_path.stat().st_size,
        ))

    return shards
