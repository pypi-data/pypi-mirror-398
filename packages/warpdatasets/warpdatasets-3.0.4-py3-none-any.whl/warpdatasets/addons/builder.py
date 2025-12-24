"""Embedding builder - compute embeddings for datasets.

Supports multiple providers:
- OpenAI (text-embedding-3-small, text-embedding-3-large, etc.)
- Sentence Transformers (local models)
- Custom callable
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal

import numpy as np

if TYPE_CHECKING:
    from warpdatasets.api.dataset import Dataset
    from warpdatasets.manifest.model import AddonDescriptor


@dataclass
class EmbeddingConfig:
    """Configuration for embedding computation."""

    provider: str  # "openai", "sentence-transformers", "custom"
    model: str  # Model identifier
    dims: int  # Expected output dimensions
    metric: str = "cosine"
    normalized: bool = True
    batch_size: int = 100  # Rows per embedding batch
    source_columns: list[str] | None = None  # Columns to embed (concatenated)

    # Provider-specific options
    api_key: str | None = None  # For OpenAI
    device: str | None = None  # For sentence-transformers ("cuda", "cpu")


class EmbeddingBuilder:
    """Builds embeddings for a dataset.

    Usage:
        builder = EmbeddingBuilder(dataset, config)
        addon = builder.build(output_dir)
    """

    def __init__(
        self,
        dataset: "Dataset",
        config: EmbeddingConfig,
        table: str = "main",
        key_column: str = "rid",
    ):
        """Initialize builder.

        Args:
            dataset: Dataset to embed
            config: Embedding configuration
            table: Table to embed
            key_column: Column to use as join key
        """
        self.dataset = dataset
        self.config = config
        self.table_name = table
        self.key_column = key_column

        # Get the embedding function
        self._embed_fn = self._get_embed_function()

    def _get_embed_function(self) -> Callable[[list[str]], np.ndarray]:
        """Get the embedding function for the configured provider."""
        if self.config.provider == "openai":
            return self._create_openai_embedder()
        elif self.config.provider == "sentence-transformers":
            return self._create_st_embedder()
        elif self.config.provider == "custom":
            raise ValueError("Custom provider requires passing embed_fn to build()")
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def _create_openai_embedder(self) -> Callable[[list[str]], np.ndarray]:
        """Create OpenAI embedding function."""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY or pass api_key)")

        client = openai.OpenAI(api_key=api_key)
        model = self.config.model

        def embed(texts: list[str]) -> np.ndarray:
            # Handle empty input
            if not texts:
                return np.zeros((0, self.config.dims), dtype=np.float32)

            response = client.embeddings.create(
                input=texts,
                model=model,
            )

            embeddings = [item.embedding for item in response.data]
            arr = np.array(embeddings, dtype=np.float32)

            # Normalize if requested
            if self.config.normalized:
                norms = np.linalg.norm(arr, axis=1, keepdims=True)
                norms = np.where(norms == 0, 1, norms)
                arr = arr / norms

            return arr

        return embed

    def _create_st_embedder(self) -> Callable[[list[str]], np.ndarray]:
        """Create Sentence Transformers embedding function."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers package required: pip install sentence-transformers"
            )

        device = self.config.device
        model = SentenceTransformer(self.config.model, device=device)

        def embed(texts: list[str]) -> np.ndarray:
            if not texts:
                return np.zeros((0, self.config.dims), dtype=np.float32)

            embeddings = model.encode(
                texts,
                normalize_embeddings=self.config.normalized,
                convert_to_numpy=True,
            )
            return embeddings.astype(np.float32)

        return embed

    def _prepare_text(self, batch: dict[str, list]) -> list[str]:
        """Prepare text from batch for embedding.

        Args:
            batch: Batch dictionary

        Returns:
            List of texts to embed
        """
        columns = self.config.source_columns
        if not columns:
            # Try to find text columns automatically
            columns = [c for c in batch.keys() if c != self.key_column]

        # Concatenate columns with space
        texts = []
        n_rows = len(batch[self.key_column])

        for i in range(n_rows):
            parts = []
            for col in columns:
                if col in batch:
                    val = batch[col][i]
                    if val is not None:
                        parts.append(str(val))
            texts.append(" ".join(parts))

        return texts

    def build(
        self,
        output_dir: Path | str,
        *,
        embed_fn: Callable[[list[str]], np.ndarray] | None = None,
        build_index: bool = False,
        index_type: str = "flat",
        progress: bool = True,
    ) -> "AddonDescriptor":
        """Build embeddings and write to output directory.

        Args:
            output_dir: Directory to write embeddings
            embed_fn: Custom embedding function (required for provider="custom")
            build_index: Whether to build a FAISS index
            index_type: Type of FAISS index ("flat", "hnsw")
            progress: Show progress bar

        Returns:
            AddonDescriptor for the built embeddings
        """
        import pyarrow as pa
        import pyarrow.parquet as pq

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use custom embed_fn if provided
        if embed_fn is not None:
            self._embed_fn = embed_fn
        elif self.config.provider == "custom":
            raise ValueError("Custom provider requires passing embed_fn")

        # Get table
        table = self.dataset.table(self.table_name)

        # Collect all embeddings
        all_keys = []
        all_vectors = []
        total_rows = 0

        # Stream batches
        batch_iter = table.batch_dicts(
            batch_size=self.config.batch_size,
            columns=[self.key_column] + (self.config.source_columns or []),
        )

        if progress:
            try:
                from tqdm import tqdm
                batch_iter = tqdm(batch_iter, desc="Computing embeddings")
            except ImportError:
                pass

        for batch in batch_iter:
            keys = batch[self.key_column]
            texts = self._prepare_text(batch)

            # Compute embeddings
            vectors = self._embed_fn(texts)

            all_keys.extend(keys)
            all_vectors.append(vectors)
            total_rows += len(keys)

        # Stack all vectors
        if all_vectors:
            vectors_array = np.vstack(all_vectors)
        else:
            vectors_array = np.zeros((0, self.config.dims), dtype=np.float32)

        # Write vectors to parquet
        vectors_path = output_dir / "vectors" / "shard-00000.parquet"
        vectors_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Arrow table
        arrow_table = pa.table({
            self.key_column: all_keys,
            "vector": [vec.tolist() for vec in vectors_array],
        })

        pq.write_table(arrow_table, vectors_path)

        # Build FAISS index if requested
        index_descriptor = None
        if build_index and len(vectors_array) > 0:
            index_descriptor = self._build_faiss_index(
                vectors_array,
                output_dir,
                index_type,
            )

        # Create addon descriptor
        from warpdatasets.manifest.model import (
            AddonDescriptor,
            KeyMapping,
            EmbeddingParams,
            TableDescriptor,
            ShardInfo,
        )

        addon = AddonDescriptor(
            kind="embeddings",
            base_table=self.table_name,
            key=KeyMapping(type="rid", column=self.key_column),
            vectors=TableDescriptor(
                format="parquet",
                shards=[
                    ShardInfo(
                        uri=str(vectors_path),
                        row_count=total_rows,
                        byte_size=vectors_path.stat().st_size,
                    ),
                ],
                schema={
                    self.key_column: "int64",
                    "vector": f"list<float>[{self.config.dims}]",
                },
                row_count=total_rows,
            ),
            params=EmbeddingParams(
                provider=self.config.provider,
                model=self.config.model,
                dims=self.config.dims,
                metric=self.config.metric,
                normalized=self.config.normalized,
                source_columns=self.config.source_columns or [],
            ),
            index=index_descriptor,
        )

        return addon

    def _build_faiss_index(
        self,
        vectors: np.ndarray,
        output_dir: Path,
        index_type: str,
    ):
        """Build FAISS index.

        Args:
            vectors: Embedding vectors
            output_dir: Output directory
            index_type: Type of index

        Returns:
            IndexDescriptor
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss package required: pip install faiss-cpu")

        from warpdatasets.manifest.model import IndexDescriptor

        dims = vectors.shape[1]
        n_vectors = vectors.shape[0]

        # Create index based on type
        if index_type == "flat":
            if self.config.metric == "cosine":
                # For normalized vectors, IP = cosine similarity
                index = faiss.IndexFlatIP(dims)
            else:
                index = faiss.IndexFlatL2(dims)
            index_meta = {"type": "Flat"}

        elif index_type == "hnsw":
            # HNSW parameters
            M = 32
            ef_construction = 200

            if self.config.metric == "cosine":
                index = faiss.IndexHNSWFlat(dims, M, faiss.METRIC_INNER_PRODUCT)
            else:
                index = faiss.IndexHNSWFlat(dims, M)

            index.hnsw.efConstruction = ef_construction
            index_meta = {"type": "HNSW", "M": M, "efConstruction": ef_construction}

        else:
            raise ValueError(f"Unknown index type: {index_type}")

        # Add vectors to index
        index.add(vectors)

        # Write index
        index_path = output_dir / "index.faiss"
        faiss.write_index(index, str(index_path))

        return IndexDescriptor(
            kind="faiss",
            uri=str(index_path),
            byte_size=index_path.stat().st_size,
            meta=index_meta,
        )


def build_embeddings(
    dataset: "Dataset",
    name: str,
    provider: str,
    model: str,
    dims: int,
    *,
    source_columns: list[str] | None = None,
    table: str = "main",
    key_column: str = "rid",
    metric: str = "cosine",
    normalized: bool = True,
    batch_size: int = 100,
    build_index: bool = False,
    index_type: str = "flat",
    output_dir: Path | str | None = None,
    api_key: str | None = None,
    device: str | None = None,
    progress: bool = True,
) -> "AddonDescriptor":
    """Build embeddings for a dataset.

    Convenience function that wraps EmbeddingBuilder.

    Args:
        dataset: Dataset to embed
        name: Addon name (e.g., "clip-vit-l14@openai")
        provider: Embedding provider ("openai", "sentence-transformers")
        model: Model identifier
        dims: Expected output dimensions
        source_columns: Columns to embed (concatenated)
        table: Table to embed
        key_column: Column to use as join key
        metric: Distance metric
        normalized: Whether to normalize vectors
        batch_size: Rows per embedding batch
        build_index: Whether to build FAISS index
        index_type: Type of FAISS index
        output_dir: Output directory (default: workspace_root/addons/...)
        api_key: API key for provider
        device: Device for local models
        progress: Show progress bar

    Returns:
        AddonDescriptor for the built embeddings
    """
    from warpdatasets.config import get_settings

    config = EmbeddingConfig(
        provider=provider,
        model=model,
        dims=dims,
        metric=metric,
        normalized=normalized,
        batch_size=batch_size,
        source_columns=source_columns,
        api_key=api_key,
        device=device,
    )

    builder = EmbeddingBuilder(
        dataset=dataset,
        config=config,
        table=table,
        key_column=key_column,
    )

    # Determine output directory
    if output_dir is None:
        settings = get_settings()
        workspace, ds_name = dataset.id.split("/", 1)
        output_dir = (
            settings.workspace_root
            / "data"
            / workspace
            / ds_name
            / dataset.version_hash[:12]
            / "addons"
            / f"embeddings--{name.replace(':', '--').replace('@', '--')}"
        )

    return builder.build(
        output_dir=output_dir,
        build_index=build_index,
        index_type=index_type,
        progress=progress,
    )
