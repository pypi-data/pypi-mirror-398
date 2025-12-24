"""Artifact index for fast member lookups.

Provides O(1) lookup of tar member locations.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pyarrow.parquet as pq


@dataclass(frozen=True)
class IndexEntry:
    """Entry from artifact index.

    Contains all information needed to read a member directly.
    """

    shard_idx: int
    payload_offset: int
    payload_size: int


class ArtifactIndex:
    """Fast lookup index for artifact members.

    Supports O(1) lookup via internal dict.
    """

    def __init__(
        self,
        entries: Dict[str, IndexEntry],
        version: int = 1,
        artifact_kind: str = "tar_shards",
    ):
        """Initialize with pre-built entries dict.

        Args:
            entries: Dict mapping ref -> IndexEntry
            version: Index format version
            artifact_kind: Kind of artifact
        """
        self._entries = entries
        self._version = version
        self._artifact_kind = artifact_kind

    @property
    def version(self) -> int:
        """Index format version."""
        return self._version

    @property
    def artifact_kind(self) -> str:
        """Kind of artifact (tar_shards)."""
        return self._artifact_kind

    def lookup(self, ref: str) -> Optional[IndexEntry]:
        """Look up a member by ref.

        Args:
            ref: Member name/path

        Returns:
            IndexEntry if found, None otherwise
        """
        return self._entries.get(ref)

    def __len__(self) -> int:
        """Number of entries in index."""
        return len(self._entries)

    def __contains__(self, ref: str) -> bool:
        """Check if ref exists in index."""
        return ref in self._entries

    @classmethod
    def from_parquet(cls, path: Path) -> "ArtifactIndex":
        """Load index from Parquet file.

        Args:
            path: Path to Parquet file

        Returns:
            ArtifactIndex instance
        """
        pf = pq.ParquetFile(path)
        table = pf.read()

        # Extract metadata
        metadata = pf.schema_arrow.metadata or {}
        version = int(metadata.get(b"index_version", b"1").decode())
        artifact_kind = metadata.get(b"artifact_kind", b"tar_shards").decode()

        # Build entries dict
        entries = {}
        for i in range(len(table)):
            ref = table["ref"][i].as_py()
            entries[ref] = IndexEntry(
                shard_idx=table["shard_idx"][i].as_py(),
                payload_offset=table["payload_offset"][i].as_py(),
                payload_size=table["payload_size"][i].as_py(),
            )

        return cls(entries, version, artifact_kind)

    @classmethod
    def from_bytes(cls, data: bytes) -> "ArtifactIndex":
        """Load index from raw bytes.

        Args:
            data: Parquet file bytes

        Returns:
            ArtifactIndex instance
        """
        pf = pq.ParquetFile(io.BytesIO(data))
        table = pf.read()

        # Extract metadata
        metadata = pf.schema_arrow.metadata or {}
        version = int(metadata.get(b"index_version", b"1").decode())
        artifact_kind = metadata.get(b"artifact_kind", b"tar_shards").decode()

        # Build entries dict
        entries = {}
        for i in range(len(table)):
            ref = table["ref"][i].as_py()
            entries[ref] = IndexEntry(
                shard_idx=table["shard_idx"][i].as_py(),
                payload_offset=table["payload_offset"][i].as_py(),
                payload_size=table["payload_size"][i].as_py(),
            )

        return cls(entries, version, artifact_kind)
