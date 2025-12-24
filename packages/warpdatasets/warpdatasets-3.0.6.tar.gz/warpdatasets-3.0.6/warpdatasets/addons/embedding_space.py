"""EmbeddingSpace - handle for embedding addon.

Provides API for accessing and searching embedding vectors.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Sequence

import numpy as np

if TYPE_CHECKING:
    import pyarrow as pa
    from warpdatasets.manifest.model import AddonDescriptor, Manifest
    from warpdatasets.config.settings import Settings
    from warpdatasets.engines.duckdb import DuckDBEngine
    from warpdatasets.cache.context import CacheContext


class EmbeddingSpace:
    """Handle to an embedding space addon.

    Provides methods for:
    - Streaming embedding vectors
    - Joining vectors back to source table
    - Similarity search (with optional ANN index)
    """

    def __init__(
        self,
        name: str,
        descriptor: "AddonDescriptor",
        manifest: "Manifest",
        settings: "Settings",
        engine: "DuckDBEngine",
        cache_context: "CacheContext | None" = None,
    ):
        """Initialize embedding space handle.

        Args:
            name: Addon name (e.g., "embeddings:clip-vit-l14@openai")
            descriptor: Addon descriptor from manifest
            manifest: Parent manifest
            settings: Configuration settings
            engine: DuckDB engine for queries
            cache_context: Optional cache context
        """
        if not descriptor.is_embedding:
            raise ValueError(f"Addon '{name}' is not an embedding space")

        self.name = name
        self.descriptor = descriptor
        self.manifest = manifest
        self._settings = settings
        self._engine = engine
        self._cache_context = cache_context

        # Lazy-loaded index
        self._index = None
        self._index_loaded = False

    @property
    def params(self):
        """Get embedding parameters."""
        return self.descriptor.params

    @property
    def dims(self) -> int:
        """Get embedding dimensionality."""
        return self.params.dims if self.params else 0

    @property
    def metric(self) -> str:
        """Get distance metric."""
        return self.params.metric if self.params else "cosine"

    @property
    def model(self) -> str:
        """Get model name."""
        return self.params.model if self.params else ""

    @property
    def provider(self) -> str:
        """Get provider name."""
        return self.params.provider if self.params else ""

    @property
    def has_index(self) -> bool:
        """Check if an ANN index is available."""
        return self.descriptor.index is not None

    @property
    def row_count(self) -> int | None:
        """Get vector count if known."""
        if self.descriptor.vectors:
            return self.descriptor.vectors.row_count
        return None

    def info(self) -> dict[str, Any]:
        """Get embedding space information.

        Returns:
            Dictionary with embedding space metadata
        """
        info = {
            "name": self.name,
            "kind": self.descriptor.kind,
            "base_table": self.descriptor.base_table,
            "key": {
                "type": self.descriptor.key.type,
                "column": self.descriptor.key.column,
            },
        }

        if self.params:
            info["params"] = {
                "provider": self.params.provider,
                "model": self.params.model,
                "dims": self.params.dims,
                "metric": self.params.metric,
                "normalized": self.params.normalized,
                "source_columns": self.params.source_columns,
            }

        if self.descriptor.vectors:
            info["vectors"] = {
                "shards": len(self.descriptor.vectors.shards),
                "row_count": self.descriptor.vectors.row_count,
            }

        if self.descriptor.index:
            info["index"] = {
                "kind": self.descriptor.index.kind,
                "byte_size": self.descriptor.index.byte_size,
            }

        return info

    def vectors(self) -> "VectorsTable":
        """Get the vectors table handle.

        Returns:
            VectorsTable for streaming and joining
        """
        if not self.descriptor.vectors:
            raise ValueError(f"Embedding space '{self.name}' has no vectors table")

        return VectorsTable(
            descriptor=self.descriptor.vectors,
            key_column=self.descriptor.key.column,
            engine=self._engine,
            cache_context=self._cache_context,
            manifest=self.manifest,
            settings=self._settings,
        )

    def search(
        self,
        query: np.ndarray | list[float],
        k: int = 10,
        *,
        use_index: bool = True,
    ) -> list[dict[str, Any]]:
        """Search for nearest neighbors.

        Args:
            query: Query vector (dims,)
            k: Number of results to return
            use_index: Whether to use ANN index if available

        Returns:
            List of dicts with {rid, distance, vector}
        """
        query = np.asarray(query, dtype=np.float32)

        if query.ndim != 1 or query.shape[0] != self.dims:
            raise ValueError(f"Query must be shape ({self.dims},), got {query.shape}")

        # Try indexed search first
        if use_index and self.has_index:
            return self._search_with_index(query, k)

        # Fall back to brute force
        return self._search_brute_force(query, k)

    def _search_with_index(
        self,
        query: np.ndarray,
        k: int,
    ) -> list[dict[str, Any]]:
        """Search using ANN index (FAISS).

        Args:
            query: Query vector
            k: Number of results

        Returns:
            Search results
        """
        if not self._index_loaded:
            self._load_index()

        if self._index is None:
            # Index not available, fall back
            return self._search_brute_force(query, k)

        # Reshape for FAISS (requires 2D)
        query_2d = query.reshape(1, -1)

        # Search
        distances, indices = self._index.search(query_2d, k)

        # Convert to results
        # Note: indices are row IDs in the vectors table
        # We need to map them back to the actual rid values
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS sentinel for not found
                continue
            results.append({
                "rank": i,
                "index": int(idx),
                "distance": float(dist),
            })

        return results

    def _search_brute_force(
        self,
        query: np.ndarray,
        k: int,
    ) -> list[dict[str, Any]]:
        """Search by scanning all vectors (no index).

        Args:
            query: Query vector
            k: Number of results

        Returns:
            Search results
        """
        # Stream all vectors and compute distances
        all_results = []

        for batch in self.vectors().batches(batch_size=10000, as_format="dict"):
            rids = batch[self.descriptor.key.column]
            vectors = batch.get("vector", [])

            for rid, vec in zip(rids, vectors):
                if vec is None:
                    continue

                vec = np.asarray(vec, dtype=np.float32)
                dist = self._compute_distance(query, vec)
                all_results.append({
                    self.descriptor.key.column: rid,
                    "distance": dist,
                })

        # Sort by distance and take top k
        all_results.sort(key=lambda x: x["distance"])
        return all_results[:k]

    def _compute_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute distance between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Distance value
        """
        if self.metric == "cosine":
            # Cosine distance = 1 - cosine_similarity
            dot = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 1.0
            return 1.0 - dot / (norm_a * norm_b)

        elif self.metric == "euclidean":
            return float(np.linalg.norm(a - b))

        elif self.metric == "dot":
            # Negative dot product (larger dot = smaller distance)
            return -float(np.dot(a, b))

        else:
            raise ValueError(f"Unknown metric: {self.metric}")

    def _load_index(self) -> None:
        """Load the ANN index from cache or remote."""
        self._index_loaded = True

        if not self.has_index:
            return

        try:
            import faiss
        except ImportError:
            # FAISS not installed, will use brute force
            return

        # Get index URI
        index_uri = self.descriptor.index.uri

        # Resolve through cache if available
        if self._cache_context is not None:
            resolved = self._cache_context.resolve_uris([index_uri])
            index_path = resolved[0]
        else:
            # Direct path (local file)
            if index_uri.startswith("file://"):
                index_path = index_uri[7:]
            elif "://" not in index_uri:
                index_path = index_uri
            else:
                # Remote URI without cache, can't load
                return

        # Load FAISS index
        if Path(index_path).exists():
            self._index = faiss.read_index(index_path)

    @staticmethod
    def compute_space_id(
        dataset_version: str,
        provider: str,
        model: str,
        dims: int,
        metric: str,
        normalized: bool,
        source_columns: list[str],
    ) -> str:
        """Compute deterministic space ID for embeddings.

        This ensures two people computing the same embedding space
        for the same dataset version get the same ID.

        Args:
            dataset_version: Dataset version hash
            provider: Embedding provider
            model: Model identifier
            dims: Embedding dimensions
            metric: Distance metric
            normalized: Whether vectors are normalized
            source_columns: Columns used for embedding

        Returns:
            Deterministic space ID (hex string)
        """
        config = {
            "dataset_version": dataset_version,
            "provider": provider,
            "model": model,
            "dims": dims,
            "metric": metric,
            "normalized": normalized,
            "source_columns": sorted(source_columns),
        }

        # Canonical JSON encoding
        config_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(config_json.encode()).hexdigest()[:16]


class VectorsTable:
    """Handle to the vectors table within an embedding space.

    Similar to Table but specialized for embedding vectors.
    """

    def __init__(
        self,
        descriptor: "TableDescriptor",
        key_column: str,
        engine: "DuckDBEngine",
        cache_context: "CacheContext | None" = None,
        manifest: "Manifest | None" = None,
        settings: "Settings | None" = None,
    ):
        """Initialize vectors table.

        Args:
            descriptor: Table descriptor
            key_column: Join key column name
            engine: DuckDB engine
            cache_context: Optional cache context
            manifest: Parent manifest (for resolving portable keys)
            settings: Settings (for resolving local:// URIs)
        """
        self.descriptor = descriptor
        self.key_column = key_column
        self._engine = engine
        self._cache_context = cache_context
        self._manifest = manifest
        self._settings = settings

    @property
    def row_count(self) -> int | None:
        """Get row count if known."""
        return self.descriptor.row_count

    @property
    def shard_count(self) -> int:
        """Get number of shards."""
        return len(self.descriptor.shards)

    def _data_locations(self) -> list[str]:
        """Get ordered list of data locations to try when resolving shard keys."""
        if self._manifest is None:
            return []

        ws, name = self._manifest.dataset.split("/", 1)
        version = self._manifest.version_hash

        locs: list[str] = []

        # Local mirror - try first if settings available
        if self._settings is not None and self._settings.mode in ("local", "hybrid", "auto"):
            local_base = f"local://data/{ws}/{name}/{version}/"
            locs.append(local_base)

        # Manifest-specified locations
        if self._manifest.locations:
            locs.extend(self._manifest.locations)

        # Derived remote location from manifest_base
        if self._settings is not None and self._settings.manifest_base:
            derived = f"{self._settings.manifest_base.rstrip('/')}/data/{ws}/{name}/{version}/"
            if derived not in locs:
                locs.append(derived)

        return locs

    def _resolve_shard_uri(self, shard) -> str:
        """Resolve a shard to a usable URI."""
        from pathlib import Path
        from warpdatasets.util.uris import join_base_and_key, local_path_from_uri, file_uri_from_path

        # Legacy: if shard has uri, use it directly
        if shard.uri is not None:
            return shard.uri

        # Portable: resolve key against locations
        key = shard.key
        if key is None:
            raise ValueError("Shard has neither uri nor key")

        workspace_root = self._settings.workspace_root if self._settings else Path.home() / ".warpdatasets"

        # Try each location in priority order
        for base in self._data_locations():
            candidate = join_base_and_key(base, key)

            # Check if it's a local-ish URI and if the file exists
            local_path = local_path_from_uri(candidate, workspace_root)
            if local_path is not None:
                if local_path.exists():
                    return file_uri_from_path(local_path)
                continue

            # Remote candidate - apply cache context if available
            if self._cache_context is not None:
                candidate = self._cache_context.resolve_uri(candidate)

            return candidate

        raise FileNotFoundError(f"No valid location found for shard key={key}")

    def _resolve_all_shards(self) -> list[str]:
        """Resolve all shards to usable URIs."""
        return [self._resolve_shard_uri(s) for s in self.descriptor.shards]

    def _resolve_local_uris(self, uris: list[str]) -> list[str]:
        """Resolve local:// URIs to file:// URIs."""
        resolved = []
        for uri in uris:
            if uri.startswith("local://") and self._settings is not None:
                path = self._settings.resolve_local_uri(uri)
                resolved.append(path.as_uri())
            else:
                resolved.append(uri)
        return resolved

    def schema(self) -> dict[str, str]:
        """Get table schema.

        Returns:
            Dictionary mapping column names to types
        """
        if self.descriptor.schema:
            return self.descriptor.schema
        resolved_uris = self._resolve_all_shards()
        resolved_uris = self._resolve_local_uris(resolved_uris)
        return self._engine.describe_schema_from_uris(resolved_uris)

    def duckdb(self):
        """Get a lazy DuckDB relation for this table.

        Returns:
            DuckDB relation (not materialized)
        """
        resolved_uris = self._resolve_all_shards()
        resolved_uris = self._resolve_local_uris(resolved_uris)
        return self._engine.create_relation_from_uris(resolved_uris)

    def batches(
        self,
        *,
        batch_size: int = 10_000,
        columns: Sequence[str] | None = None,
        limit: int | None = None,
        as_format: str = "arrow",
    ) -> Iterator:
        """Stream batches of vectors.

        Args:
            batch_size: Rows per batch
            columns: Columns to include
            limit: Maximum rows
            as_format: Output format ("arrow" or "dict")

        Yields:
            Arrow RecordBatch or dict
        """
        from warpdatasets.streaming.batching import build_batch_query, stream_batches

        # Resolve all shard URIs (handles both legacy uri and portable key)
        uris = self._resolve_all_shards()

        # Resolve through cache if available
        if self._cache_context is not None:
            resolved_uris = self._cache_context.resolve_uris(uris)
        else:
            resolved_uris = list(uris)

        # Resolve local:// URIs to file:// paths
        resolved_uris = self._resolve_local_uris(resolved_uris)

        # Build query
        query = build_batch_query(
            uris=resolved_uris,
            columns=list(columns) if columns else None,
            limit=limit,
        )

        # Stream
        conn = self._engine._get_connection()
        return stream_batches(conn, query, batch_size, as_format)
