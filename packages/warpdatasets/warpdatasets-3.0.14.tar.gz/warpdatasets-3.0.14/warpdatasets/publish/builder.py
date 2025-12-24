"""Manifest builder for publishing datasets.

Builds deterministic manifests from local inputs.
"""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import pyarrow.parquet as pq

from warpdatasets.manifest.model import (
    ArtifactDescriptor,
    Binding,
    Manifest,
    ShardInfo,
    TableDescriptor,
)
from warpdatasets.publish.packer import TarShard
from warpdatasets.publish.plan import PublishPlan, UploadItem
from warpdatasets.artifacts.tar.index_builder import (
    build_tar_index,
    write_index_parquet,
)


@dataclass
class TableInput:
    """Input for a table to publish."""

    name: str
    shard_paths: list[Path]
    schema: dict[str, str] | None = None


@dataclass
class ArtifactInput:
    """Input for an artifact to publish."""

    name: str
    tar_shards: list[TarShard]
    compression: str | None = None
    build_index: bool = True  # Whether to build artifact index


@dataclass
class BindingInput:
    """Input for a binding."""

    table: str
    column: str
    artifact: str
    media_type: str
    ref_type: str


class ManifestBuilder:
    """Builder for creating publishable manifests.

    Constructs deterministic manifests from local parquet files
    and artifact tar shards.
    """

    def __init__(
        self,
        dataset_id: str,
        base_uri: str,
        metadata: dict | None = None,
        temp_dir: Path | None = None,
    ):
        """Initialize manifest builder.

        Args:
            dataset_id: Dataset identifier (workspace/name)
            base_uri: Base URI for storage (e.g., s3://bucket/warp)
            metadata: Optional metadata dict (not included in hash)
            temp_dir: Optional temp directory for index files
        """
        self._dataset_id = dataset_id
        self._base_uri = base_uri.rstrip("/")
        self._meta = metadata or {}
        self._temp_dir = temp_dir

        self._tables: list[TableInput] = []
        self._artifacts: list[ArtifactInput] = []
        self._bindings: list[BindingInput] = []
        self._index_files: dict[str, Path] = {}  # artifact_name -> index path

    def add_table(
        self,
        name: str,
        shard_paths: Sequence[Path],
        schema: dict[str, str] | None = None,
    ) -> "ManifestBuilder":
        """Add a table to the manifest.

        Args:
            name: Table name (typically "main")
            shard_paths: Paths to parquet shard files
            schema: Optional schema dict (inferred from parquet if None)

        Returns:
            Self for chaining
        """
        # Sort paths for determinism
        sorted_paths = sorted(shard_paths, key=lambda p: p.name)
        self._tables.append(TableInput(
            name=name,
            shard_paths=[Path(p) for p in sorted_paths],
            schema=schema,
        ))
        return self

    def add_artifact(
        self,
        name: str,
        tar_shards: Sequence[TarShard],
        compression: str | None = None,
        build_index: bool = True,
    ) -> "ManifestBuilder":
        """Add an artifact to the manifest.

        Args:
            name: Artifact name
            tar_shards: Packed tar shards from packer
            compression: Compression type (None for uncompressed)
            build_index: Whether to build artifact index (default: True)

        Returns:
            Self for chaining
        """
        self._artifacts.append(ArtifactInput(
            name=name,
            tar_shards=list(tar_shards),
            compression=compression,
            build_index=build_index,
        ))
        return self

    def add_binding(
        self,
        table: str,
        column: str,
        artifact: str,
        media_type: str = "file",
        ref_type: str = "tar_member_path",
    ) -> "ManifestBuilder":
        """Add a binding between a table column and artifact.

        Args:
            table: Table name
            column: Column name containing references
            artifact: Artifact name
            media_type: Media type (file, image, audio)
            ref_type: Reference type (tar_member_path)

        Returns:
            Self for chaining
        """
        self._bindings.append(BindingInput(
            table=table,
            column=column,
            artifact=artifact,
            media_type=media_type,
            ref_type=ref_type,
        ))
        return self

    def build(self) -> Manifest:
        """Build the manifest.

        Returns:
            Complete Manifest object with target URIs
        """
        return self.build_plan().manifest

    def build_plan(self) -> PublishPlan:
        """Build a complete publish plan.

        Returns:
            PublishPlan with manifest and upload items
        """
        # First pass: build manifest with placeholder URIs to compute hash
        tables = self._build_tables_with_placeholders()
        artifacts = self._build_artifacts_with_placeholders()
        bindings = self._build_bindings()

        # Create preliminary manifest to get version hash
        preliminary = Manifest(
            dataset=self._dataset_id,
            tables=tables,
            artifacts=artifacts,
            bindings=bindings,
            meta=self._meta,
        )
        version_hash = preliminary.version_hash

        # Second pass: build manifest with portable keys (not full URIs)
        table_uploads = []
        final_tables = {}

        for table_input in self._tables:
            shards = []
            for i, shard_path in enumerate(table_input.shard_paths):
                # Compute portable key and full target URI
                key = self._table_shard_key(table_input.name, i)
                target_uri = self._table_shard_uri(
                    table_input.name, i, version_hash
                )

                # Get size from file
                size = shard_path.stat().st_size

                # Use key (portable) instead of uri (machine-specific)
                shards.append(ShardInfo(
                    key=key,
                    byte_size=size,
                ))

                table_uploads.append(UploadItem(
                    source_path=shard_path,
                    target_uri=target_uri,
                    size_bytes=size,
                ))

            # Infer schema and row_count from parquet
            schema = table_input.schema
            row_count = 0
            if table_input.shard_paths:
                first_shard = pq.ParquetFile(table_input.shard_paths[0])
                if schema is None:
                    schema = {
                        f.name: str(f.type) for f in first_shard.schema_arrow
                    }
                # Sum row counts from all shards
                for shard_path in table_input.shard_paths:
                    pf = pq.ParquetFile(shard_path)
                    row_count += pf.metadata.num_rows

            final_tables[table_input.name] = TableDescriptor(
                format="parquet",
                shards=shards,
                schema=schema,
                row_count=row_count,
            )

        # Build artifacts with portable keys and indices
        artifact_uploads = []
        index_uploads = []
        final_artifacts = {}

        for artifact_input in self._artifacts:
            shards = []
            for i, tar_shard in enumerate(artifact_input.tar_shards):
                # Compute portable key and full target URI
                key = self._artifact_shard_key(artifact_input.name, i)
                target_uri = self._artifact_shard_uri(
                    artifact_input.name, i, version_hash
                )

                size = tar_shard.size_bytes

                # Use key (portable) instead of uri (machine-specific)
                shards.append(ShardInfo(
                    key=key,
                    byte_size=size,
                ))

                artifact_uploads.append(UploadItem(
                    source_path=tar_shard.path,
                    target_uri=target_uri,
                    size_bytes=size,
                ))

            # Build index if requested
            index_info = None
            if artifact_input.build_index and artifact_input.tar_shards:
                index_path, index_uri = self._build_artifact_index(
                    artifact_input, version_hash
                )
                index_size = index_path.stat().st_size
                # Use portable key for index
                index_key = self._artifact_index_key(artifact_input.name)
                index_info = ShardInfo(key=index_key, byte_size=index_size)
                index_uploads.append(UploadItem(
                    source_path=index_path,
                    target_uri=index_uri,
                    size_bytes=index_size,
                ))

            final_artifacts[artifact_input.name] = ArtifactDescriptor(
                kind="tar_shards",
                shards=shards,
                compression=artifact_input.compression,
                index=index_info,
            )

        # Compute data location base URI (where shard keys are resolved)
        data_base = f"{self._base_uri}/data/{self._dataset_id}/{version_hash}/"

        # Create final manifest with locations
        manifest = Manifest(
            dataset=self._dataset_id,
            tables=final_tables,
            artifacts=final_artifacts,
            bindings=bindings,
            meta=self._meta,
            locations=[data_base],  # Remote location for resolving keys
        )

        # Create plan
        manifest_uri = self._manifest_uri(version_hash)
        latest_uri = self._latest_uri()

        return PublishPlan(
            manifest=manifest,
            version=version_hash,
            manifest_uri=manifest_uri,
            latest_uri=latest_uri,
            table_uploads=table_uploads,
            artifact_uploads=artifact_uploads,
            index_uploads=index_uploads,
        )

    def _build_tables_with_placeholders(self) -> dict[str, TableDescriptor]:
        """Build tables with placeholder URIs for hash computation."""
        tables = {}
        for table_input in self._tables:
            shards = []
            row_count = 0
            schema = table_input.schema

            for i, shard_path in enumerate(table_input.shard_paths):
                # Use content hash as placeholder for determinism
                content_hash = self._file_content_hash(shard_path)
                size = shard_path.stat().st_size

                shards.append(ShardInfo(
                    uri=f"hash://{content_hash}",
                    byte_size=size,
                ))

                # Get row count
                pf = pq.ParquetFile(shard_path)
                row_count += pf.metadata.num_rows

                # Infer schema from first shard
                if schema is None and i == 0:
                    schema = {
                        f.name: str(f.type) for f in pf.schema_arrow
                    }

            tables[table_input.name] = TableDescriptor(
                format="parquet",
                shards=shards,
                schema=schema,
                row_count=row_count,
            )

        return tables

    def _build_artifacts_with_placeholders(self) -> dict[str, ArtifactDescriptor]:
        """Build artifacts with placeholder URIs for hash computation."""
        artifacts = {}
        for artifact_input in self._artifacts:
            shards = []
            for tar_shard in artifact_input.tar_shards:
                content_hash = self._file_content_hash(tar_shard.path)
                shards.append(ShardInfo(
                    uri=f"hash://{content_hash}",
                    byte_size=tar_shard.size_bytes,
                ))

            artifacts[artifact_input.name] = ArtifactDescriptor(
                kind="tar_shards",
                shards=shards,
                compression=artifact_input.compression,
            )

        return artifacts

    def _build_bindings(self) -> list[Binding]:
        """Build binding objects."""
        return [
            Binding(
                table=b.table,
                column=b.column,
                artifact=b.artifact,
                ref_type=b.ref_type,
                media_type=b.media_type,
            )
            for b in self._bindings
        ]

    def _file_content_hash(self, path: Path) -> str:
        """Compute content hash of a file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _table_shard_key(self, table_name: str, index: int) -> str:
        """Generate portable key for a table shard."""
        return f"tables/{table_name}/shard-{index:05d}.parquet"

    def _table_shard_uri(self, table_name: str, index: int, version: str) -> str:
        """Generate full URI for a table shard (for uploads)."""
        key = self._table_shard_key(table_name, index)
        return f"{self._base_uri}/data/{self._dataset_id}/{version}/{key}"

    def _artifact_shard_key(self, artifact_name: str, index: int) -> str:
        """Generate portable key for an artifact shard."""
        return f"artifacts/{artifact_name}/shard-{index:05d}.tar"

    def _artifact_shard_uri(self, artifact_name: str, index: int, version: str) -> str:
        """Generate full URI for an artifact shard (for uploads)."""
        key = self._artifact_shard_key(artifact_name, index)
        return f"{self._base_uri}/data/{self._dataset_id}/{version}/{key}"

    def _artifact_index_key(self, artifact_name: str) -> str:
        """Generate portable key for an artifact index."""
        return f"artifacts/{artifact_name}/index.parquet"

    def _manifest_uri(self, version: str) -> str:
        """Generate URI for the manifest."""
        return f"{self._base_uri}/manifests/{self._dataset_id}/{version}.json"

    def _latest_uri(self) -> str:
        """Generate URI for the latest pointer."""
        return f"{self._base_uri}/manifests/{self._dataset_id}/latest.json"

    def _artifact_index_uri(self, artifact_name: str, version: str) -> str:
        """Generate URI for an artifact index."""
        return (
            f"{self._base_uri}/data/{self._dataset_id}/{version}/"
            f"artifacts/{artifact_name}/index.parquet"
        )

    def _build_artifact_index(
        self, artifact_input: ArtifactInput, version_hash: str
    ) -> tuple[Path, str]:
        """Build artifact index and return (local_path, target_uri).

        Args:
            artifact_input: Artifact input with tar shards
            version_hash: Version hash for URI generation

        Returns:
            Tuple of (local index path, target URI)
        """
        # Determine temp directory
        if self._temp_dir is not None:
            temp_dir = self._temp_dir
            temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Use same directory as first tar shard
            temp_dir = artifact_input.tar_shards[0].path.parent

        # Build index
        tar_paths = [shard.path for shard in artifact_input.tar_shards]
        index_entries = build_tar_index(tar_paths)

        # Write to temp file
        index_path = temp_dir / f"{artifact_input.name}_index.parquet"
        write_index_parquet(
            index_entries,
            index_path,
            version=1,
            artifact_kind="tar_shards",
        )

        # Store for later cleanup if needed
        self._index_files[artifact_input.name] = index_path

        # Generate target URI
        target_uri = self._artifact_index_uri(artifact_input.name, version_hash)

        return index_path, target_uri
