"""Manifest data model.

Defines the structure of dataset manifests with support for:
- Tables (Parquet shards)
- Artifacts (raw data shards) - placeholder for Phase 3
- Bindings (table-to-artifact linkage) - placeholder for Phase 3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShardInfo:
    """Information about a single shard (parquet file or artifact blob).

    Supports two modes:
    - Legacy: uri field contains absolute URI (file://, s3://, etc.)
    - Portable: key field contains relative path, resolved against manifest.locations
    """

    # NEW: portable relative key, e.g. "tables/main/shard-00000.parquet"
    key: str | None = None

    # LEGACY: absolute URI, kept for backward compatibility
    uri: str | None = None

    hash: str | None = None
    row_count: int | None = None
    byte_size: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {}
        if self.key is not None:
            result["key"] = self.key
        if self.uri is not None:
            result["uri"] = self.uri
        if self.hash is not None:
            result["hash"] = self.hash
        if self.row_count is not None:
            result["row_count"] = self.row_count
        if self.byte_size is not None:
            result["byte_size"] = self.byte_size
        return result

    @property
    def effective_uri(self) -> str | None:
        """Get effective URI (legacy uri field or None if only key is set)."""
        return self.uri


@dataclass
class TableDescriptor:
    """Descriptor for a table in the manifest."""

    format: str  # Currently only "parquet" supported
    shards: list[ShardInfo]
    schema: dict[str, str] | None = None
    row_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "format": self.format,
            "shards": [s.to_dict() for s in self.shards],
        }
        if self.schema is not None:
            result["schema"] = self.schema
        if self.row_count is not None:
            result["row_count"] = self.row_count
        return result

    @property
    def uris(self) -> list[str]:
        """Get list of shard URIs (legacy - only returns shards with uri set)."""
        return [s.uri for s in self.shards if s.uri is not None]

    @property
    def keys(self) -> list[str]:
        """Get list of shard keys (portable - only returns shards with key set)."""
        return [s.key for s in self.shards if s.key is not None]

    @property
    def is_portable(self) -> bool:
        """Check if this table uses portable keys (vs legacy URIs)."""
        return any(s.key is not None for s in self.shards)


@dataclass
class ArtifactDescriptor:
    """Descriptor for an artifact (raw data).

    Represents raw payload storage (images, audio, files) as tar shards.
    """

    kind: str  # "tar_shards"
    shards: list[ShardInfo]
    compression: str | None = None  # "none", "gzip", "zstd" (Phase 3: only "none" supported)
    index: ShardInfo | None = None  # Optional index for fast member lookup (Phase 6)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "kind": self.kind,
            "shards": [s.to_dict() for s in self.shards],
        }
        if self.compression is not None:
            result["compression"] = self.compression
        if self.index is not None:
            result["index"] = self.index.to_dict()
        return result

    @property
    def uris(self) -> list[str]:
        """Get list of shard URIs (legacy - only returns shards with uri set)."""
        return [s.uri for s in self.shards if s.uri is not None]

    @property
    def keys(self) -> list[str]:
        """Get list of shard keys (portable - only returns shards with key set)."""
        return [s.key for s in self.shards if s.key is not None]

    @property
    def is_portable(self) -> bool:
        """Check if this artifact uses portable keys (vs legacy URIs)."""
        return any(s.key is not None for s in self.shards)


@dataclass
class Binding:
    """Binding between a table column and an artifact.

    Links a column in a table to an artifact, enabling typed reference resolution.
    """

    table: str
    column: str
    artifact: str
    ref_type: str  # "tar_member_path" - how to interpret column values
    media_type: str = "file"  # "image", "audio", "file" - controls typed ref class

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "table": self.table,
            "column": self.column,
            "artifact": self.artifact,
            "ref_type": self.ref_type,
            "media_type": self.media_type,
        }


@dataclass
class KeyMapping:
    """Defines how an addon joins back to its base table.

    Specifies the key type and column(s) used for joining addon data
    back to the original table rows.
    """

    type: str  # "rid" (row id), "column", "composite"
    column: str  # Column name in both tables for joining

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type,
            "column": self.column,
        }


@dataclass
class IndexDescriptor:
    """Descriptor for an ANN index (FAISS, etc.).

    Represents an optional nearest-neighbor index for fast similarity search.
    """

    kind: str  # "faiss", "annoy", "hnsw", etc.
    uri: str | None = None  # Legacy: absolute URI
    key: str | None = None  # Portable: relative key
    byte_size: int | None = None
    meta: dict[str, Any] | None = None  # Index-specific params (M, efConstruction, etc.)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "kind": self.kind,
        }
        if self.uri is not None:
            result["uri"] = self.uri
        if self.key is not None:
            result["key"] = self.key
        if self.byte_size is not None:
            result["byte_size"] = self.byte_size
        if self.meta is not None:
            result["meta"] = self.meta
        return result


@dataclass
class EmbeddingParams:
    """Parameters for an embedding space.

    Captures all configuration needed to reproduce embeddings.
    """

    provider: str  # "openai", "sentence-transformers", "custom"
    model: str  # Model identifier
    dims: int  # Embedding dimensionality
    metric: str = "cosine"  # "cosine", "euclidean", "dot"
    normalized: bool = True  # Whether vectors are L2-normalized
    source_columns: list[str] = field(default_factory=list)  # Columns used to compute embedding

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "provider": self.provider,
            "model": self.model,
            "dims": self.dims,
            "metric": self.metric,
            "normalized": self.normalized,
            "source_columns": self.source_columns,
        }


@dataclass
class AddonDescriptor:
    """Descriptor for a dataset addon (embeddings, splits, labels, etc.).

    Addons are supplementary data attached to a dataset version. They can include:
    - Sidecar tables (Parquet keyed by rid)
    - Sidecar artifacts (FAISS index, metadata)
    - Composite (table + artifacts)

    Examples:
    - embeddings: vectors table + optional ANN index
    - splits: table with {rid, split} columns
    - labels: table with {rid, label, confidence} columns
    """

    kind: str  # "embeddings", "splits", "labels", "eval", etc.
    base_table: str  # Which table this addon extends
    key: KeyMapping  # How to join back to base table

    # For table-based addons (embeddings vectors, splits, labels)
    vectors: TableDescriptor | None = None  # Primary data table

    # For embedding addons specifically
    params: EmbeddingParams | None = None

    # Optional ANN index for embeddings
    index: IndexDescriptor | None = None

    # Generic metadata
    meta: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "kind": self.kind,
            "base_table": self.base_table,
            "key": self.key.to_dict(),
        }
        if self.vectors is not None:
            result["vectors"] = self.vectors.to_dict()
        if self.params is not None:
            result["params"] = self.params.to_dict()
        if self.index is not None:
            result["index"] = self.index.to_dict()
        if self.meta is not None:
            result["meta"] = self.meta
        return result

    @property
    def is_embedding(self) -> bool:
        """Check if this addon is an embedding space."""
        return self.kind == "embeddings"


@dataclass
class Manifest:
    """Dataset manifest - the source of truth for a dataset version.

    A manifest is immutable once published. The version hash is derived
    deterministically from its content (excluding the 'meta' and 'locations' envelopes).
    """

    dataset: str  # Format: "workspace/name"
    tables: dict[str, TableDescriptor]
    artifacts: dict[str, ArtifactDescriptor] = field(default_factory=dict)
    bindings: list[Binding] = field(default_factory=list)
    addons: dict[str, AddonDescriptor] = field(default_factory=dict)  # Phase 8: addons
    schema: dict[str, str] | None = None  # Global schema hint
    row_count: int | None = None  # Total rows across all tables
    meta: dict[str, Any] | None = None  # Non-hashed metadata (created_at, etc.)

    # NEW: Data locations (non-hashed) - base URIs where shard keys are resolved
    # Example: ["s3://bucket/warp/data/ws/name/{version}/", "local://data/ws/name/{version}/"]
    locations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to full dictionary including meta and locations."""
        result = self.to_hashable_dict()
        if self.locations:
            result["locations"] = self.locations
        if self.meta:
            result["meta"] = self.meta
        return result

    @property
    def is_portable(self) -> bool:
        """Check if this manifest uses portable keys (vs legacy URIs)."""
        return any(t.is_portable for t in self.tables.values())

    def to_hashable_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing (excludes 'meta')."""
        result: dict[str, Any] = {
            "dataset": self.dataset,
            "tables": {name: table.to_dict() for name, table in self.tables.items()},
        }

        if self.artifacts:
            result["artifacts"] = {
                name: artifact.to_dict() for name, artifact in self.artifacts.items()
            }

        if self.bindings:
            result["bindings"] = [b.to_dict() for b in self.bindings]

        if self.addons:
            result["addons"] = {
                name: addon.to_dict() for name, addon in self.addons.items()
            }

        if self.schema is not None:
            result["schema"] = self.schema

        if self.row_count is not None:
            result["row_count"] = self.row_count

        return result

    @property
    def version_hash(self) -> str:
        """Compute deterministic version hash from manifest content."""
        from warpdatasets.manifest.canon import compute_version_hash

        return compute_version_hash(self.to_hashable_dict())

    @classmethod
    def _parse_shard(cls, s: dict | str) -> ShardInfo:
        """Parse a shard entry from dict or legacy string format."""
        if isinstance(s, str):
            # Legacy: bare URI string
            return ShardInfo(uri=s)
        # Dict format - supports both uri (legacy) and key (portable)
        return ShardInfo(
            key=s.get("key"),
            uri=s.get("uri"),
            hash=s.get("hash"),
            row_count=s.get("row_count"),
            byte_size=s.get("byte_size"),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        """Create a Manifest from a dictionary.

        Supports both legacy (uri-based) and portable (key-based) manifests.
        """
        tables = {}
        for name, table_data in data.get("tables", {}).items():
            shards = [
                cls._parse_shard(s)
                for s in table_data.get("shards", table_data.get("uris", []))
            ]
            tables[name] = TableDescriptor(
                format=table_data.get("format", "parquet"),
                shards=shards,
                schema=table_data.get("schema"),
                row_count=table_data.get("row_count"),
            )

        artifacts = {}
        for name, artifact_data in data.get("artifacts", {}).items():
            shards = [
                cls._parse_shard(s)
                for s in artifact_data.get("shards", [])
            ]
            index = None
            if artifact_data.get("index"):
                idx = artifact_data["index"]
                index = ShardInfo(
                    key=idx.get("key"),
                    uri=idx.get("uri"),
                    hash=idx.get("hash"),
                    byte_size=idx.get("byte_size"),
                )
            artifacts[name] = ArtifactDescriptor(
                kind=artifact_data["kind"],
                shards=shards,
                compression=artifact_data.get("compression"),
                index=index,
            )

        bindings = [
            Binding(
                table=b["table"],
                column=b["column"],
                artifact=b["artifact"],
                ref_type=b["ref_type"],
                media_type=b.get("media_type", "file"),
            )
            for b in data.get("bindings", [])
        ]

        # Parse addons
        addons = {}
        for name, addon_data in data.get("addons", {}).items():
            # Parse key mapping
            key_data = addon_data["key"]
            key = KeyMapping(
                type=key_data["type"],
                column=key_data["column"],
            )

            # Parse vectors table if present
            vectors = None
            if addon_data.get("vectors"):
                vec_data = addon_data["vectors"]
                vec_shards = [
                    cls._parse_shard(s)
                    for s in vec_data.get("shards", [])
                ]
                vectors = TableDescriptor(
                    format=vec_data.get("format", "parquet"),
                    shards=vec_shards,
                    schema=vec_data.get("schema"),
                    row_count=vec_data.get("row_count"),
                )

            # Parse embedding params if present
            params = None
            if addon_data.get("params"):
                p = addon_data["params"]
                params = EmbeddingParams(
                    provider=p["provider"],
                    model=p["model"],
                    dims=p["dims"],
                    metric=p.get("metric", "cosine"),
                    normalized=p.get("normalized", True),
                    source_columns=p.get("source_columns", []),
                )

            # Parse index if present
            index = None
            if addon_data.get("index"):
                idx = addon_data["index"]
                index = IndexDescriptor(
                    kind=idx["kind"],
                    uri=idx.get("uri"),
                    key=idx.get("key"),
                    byte_size=idx.get("byte_size"),
                    meta=idx.get("meta"),
                )

            addons[name] = AddonDescriptor(
                kind=addon_data["kind"],
                base_table=addon_data["base_table"],
                key=key,
                vectors=vectors,
                params=params,
                index=index,
                meta=addon_data.get("meta"),
            )

        return cls(
            dataset=data["dataset"],
            tables=tables,
            artifacts=artifacts,
            bindings=bindings,
            addons=addons,
            schema=data.get("schema"),
            row_count=data.get("row_count"),
            meta=data.get("meta"),
            locations=data.get("locations") or [],
        )
