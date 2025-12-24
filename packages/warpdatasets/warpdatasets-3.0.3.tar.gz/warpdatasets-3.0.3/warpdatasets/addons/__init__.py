"""Addons module for warpdatasets.

Provides support for supplementary data attached to datasets:
- Embeddings (vector spaces with optional ANN index)
- Splits (train/val/test assignments)
- Labels (supplementary annotations)
- Evaluations (model scores, metrics)
"""

from warpdatasets.addons.embedding_space import EmbeddingSpace
from warpdatasets.addons.builder import (
    EmbeddingBuilder,
    EmbeddingConfig,
    build_embeddings,
)
from warpdatasets.addons.publish import (
    publish_addon,
    update_manifest_with_addon,
    save_manifest,
)

__all__ = [
    "EmbeddingSpace",
    "EmbeddingBuilder",
    "EmbeddingConfig",
    "build_embeddings",
    "publish_addon",
    "update_manifest_with_addon",
    "save_manifest",
]
