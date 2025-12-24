"""Publish plan for dataset uploads.

Defines the plan structure for what needs to be uploaded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from warpdatasets.manifest.model import Manifest


@dataclass
class UploadItem:
    """A single item to upload."""

    source_path: Path
    target_uri: str
    size_bytes: int

    @property
    def size(self) -> int:
        """Alias for size_bytes."""
        return self.size_bytes


@dataclass
class PublishPlan:
    """Complete plan for publishing a dataset version.

    Contains the manifest, all upload items, and target URIs.
    """

    # The manifest to publish
    manifest: "Manifest"

    # Content-based version hash (used in URIs, deterministic from content)
    version: str

    # Target URIs
    manifest_uri: str
    latest_uri: str

    # Uploads organized by type
    table_uploads: list[UploadItem] = field(default_factory=list)
    artifact_uploads: list[UploadItem] = field(default_factory=list)
    index_uploads: list[UploadItem] = field(default_factory=list)

    @property
    def all_uploads(self) -> list[UploadItem]:
        """Get all upload items."""
        return self.table_uploads + self.artifact_uploads + self.index_uploads

    @property
    def data_uploads(self) -> list[UploadItem]:
        """Get data shard uploads (tables + artifacts, excludes indices)."""
        return self.table_uploads + self.artifact_uploads

    @property
    def total_bytes(self) -> int:
        """Total bytes to upload."""
        return sum(item.size_bytes for item in self.all_uploads)

    @property
    def shard_count(self) -> int:
        """Total number of data shards (excludes indices)."""
        return len(self.data_uploads)

    @property
    def index_count(self) -> int:
        """Number of index files."""
        return len(self.index_uploads)

    @property
    def table_shard_count(self) -> int:
        """Number of table shards."""
        return len(self.table_uploads)

    @property
    def artifact_shard_count(self) -> int:
        """Number of artifact shards."""
        return len(self.artifact_uploads)

    def summary(self) -> str:
        """Get human-readable summary of the plan."""
        lines = [
            f"Dataset: {self.manifest.dataset}",
            f"Version: {self.version}",
            "",
            "Tables:",
        ]

        for table_name, table_desc in self.manifest.tables.items():
            lines.append(f"  {table_name}: {len(table_desc.shards)} shards")

        if self.manifest.artifacts:
            lines.append("")
            lines.append("Artifacts:")
            for art_name, art_desc in self.manifest.artifacts.items():
                idx_info = " (indexed)" if art_desc.index else ""
                lines.append(f"  {art_name}: {len(art_desc.shards)} shards{idx_info}")

        if self.manifest.bindings:
            lines.append("")
            lines.append("Bindings:")
            for binding in self.manifest.bindings:
                lines.append(
                    f"  {binding.table}.{binding.column} -> "
                    f"{binding.artifact}:{binding.media_type}"
                )

        lines.extend([
            "",
            f"Total shards: {self.shard_count}",
            f"Total bytes: {self._format_bytes(self.total_bytes)}",
            "",
            f"Manifest URI: {self.manifest_uri}",
            f"Latest URI: {self.latest_uri}",
        ])

        return "\n".join(lines)

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable string."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
