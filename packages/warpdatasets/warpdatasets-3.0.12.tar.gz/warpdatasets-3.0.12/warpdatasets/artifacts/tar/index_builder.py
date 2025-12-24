"""Tar index builder for artifact shards.

Builds a deterministic index mapping member names to shard locations.
"""

from __future__ import annotations

import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pyarrow as pa
import pyarrow.parquet as pq


@dataclass
class TarMemberInfo:
    """Information about a tar member for indexing."""

    ref: str
    shard_idx: int
    payload_offset: int
    payload_size: int


def build_tar_index(
    tar_paths: Sequence[Path],
) -> list[dict]:
    """Build index from tar shard files.

    Scans each tar file and records member locations.

    Args:
        tar_paths: Ordered list of tar shard paths

    Returns:
        List of index entries as dicts
    """
    entries = []

    for shard_idx, tar_path in enumerate(tar_paths):
        with tarfile.open(tar_path, "r") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue

                # Tar header is 512 bytes, data starts after header
                # member.offset is the header offset
                # member.offset_data is the actual data offset
                payload_offset = member.offset_data
                payload_size = member.size

                entries.append({
                    "ref": member.name,
                    "shard_idx": shard_idx,
                    "payload_offset": payload_offset,
                    "payload_size": payload_size,
                })

    # Sort by ref for determinism
    entries.sort(key=lambda e: e["ref"])
    return entries


def write_index_parquet(
    entries: list[dict],
    output_path: Path,
    version: int = 1,
    artifact_kind: str = "tar_shards",
) -> None:
    """Write index entries to Parquet file.

    Args:
        entries: List of index entries from build_tar_index
        output_path: Path to write Parquet file
        version: Index format version
        artifact_kind: Kind of artifact (tar_shards)
    """
    if not entries:
        # Create empty table with correct schema
        schema = pa.schema([
            pa.field("ref", pa.string()),
            pa.field("shard_idx", pa.int32()),
            pa.field("payload_offset", pa.int64()),
            pa.field("payload_size", pa.int64()),
        ])
        table = pa.table({
            "ref": pa.array([], type=pa.string()),
            "shard_idx": pa.array([], type=pa.int32()),
            "payload_offset": pa.array([], type=pa.int64()),
            "payload_size": pa.array([], type=pa.int64()),
        })
    else:
        table = pa.table({
            "ref": [e["ref"] for e in entries],
            "shard_idx": [e["shard_idx"] for e in entries],
            "payload_offset": [e["payload_offset"] for e in entries],
            "payload_size": [e["payload_size"] for e in entries],
        })

    # Add metadata
    metadata = {
        b"index_version": str(version).encode(),
        b"artifact_kind": artifact_kind.encode(),
    }
    schema_with_meta = table.schema.with_metadata(metadata)
    table = table.cast(schema_with_meta)

    # Write to parquet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output_path)


def load_index_parquet(path: Path) -> list[dict]:
    """Load index entries from Parquet file.

    Args:
        path: Path to Parquet file

    Returns:
        List of index entries as dicts
    """
    table = pq.read_table(path)
    entries = []
    for i in range(len(table)):
        entries.append({
            "ref": table["ref"][i].as_py(),
            "shard_idx": table["shard_idx"][i].as_py(),
            "payload_offset": table["payload_offset"][i].as_py(),
            "payload_size": table["payload_size"][i].as_py(),
        })
    return entries
