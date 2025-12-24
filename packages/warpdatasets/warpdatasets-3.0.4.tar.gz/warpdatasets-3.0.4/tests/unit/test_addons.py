"""Tests for addon system (Phase 8).

Tests for addons, embeddings, and related functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from warpdatasets.manifest.model import (
    Manifest,
    TableDescriptor,
    ShardInfo,
    AddonDescriptor,
    KeyMapping,
    EmbeddingParams,
    IndexDescriptor,
)
from warpdatasets.addons import EmbeddingSpace
from warpdatasets.config.settings import Settings


# Fixtures


@pytest.fixture
def embedding_addon() -> AddonDescriptor:
    """Create an embedding addon descriptor."""
    return AddonDescriptor(
        kind="embeddings",
        base_table="main",
        key=KeyMapping(type="rid", column="rid"),
        vectors=TableDescriptor(
            format="parquet",
            shards=[
                ShardInfo(
                    uri="s3://bucket/addons/clip/vectors/shard-00000.parquet",
                    row_count=1000,
                ),
            ],
            schema={"rid": "int64", "vector": "list<float>"},
            row_count=1000,
        ),
        params=EmbeddingParams(
            provider="openai",
            model="clip-vit-l14",
            dims=768,
            metric="cosine",
            normalized=True,
            source_columns=["image_path"],
        ),
    )


@pytest.fixture
def embedding_addon_with_index() -> AddonDescriptor:
    """Create an embedding addon with FAISS index."""
    return AddonDescriptor(
        kind="embeddings",
        base_table="main",
        key=KeyMapping(type="rid", column="rid"),
        vectors=TableDescriptor(
            format="parquet",
            shards=[
                ShardInfo(
                    uri="s3://bucket/addons/clip/vectors/shard-00000.parquet",
                    row_count=1000,
                ),
            ],
            schema={"rid": "int64", "vector": "list<float>"},
            row_count=1000,
        ),
        params=EmbeddingParams(
            provider="openai",
            model="clip-vit-l14",
            dims=768,
            metric="cosine",
            normalized=True,
            source_columns=["image_path"],
        ),
        index=IndexDescriptor(
            kind="faiss",
            uri="s3://bucket/addons/clip/index.faiss",
            byte_size=1024000,
            meta={"type": "HNSW", "M": 32},
        ),
    )


@pytest.fixture
def splits_addon() -> AddonDescriptor:
    """Create a splits addon descriptor."""
    return AddonDescriptor(
        kind="splits",
        base_table="main",
        key=KeyMapping(type="rid", column="rid"),
        vectors=TableDescriptor(
            format="parquet",
            shards=[
                ShardInfo(
                    uri="s3://bucket/addons/splits/data.parquet",
                    row_count=1000,
                ),
            ],
            schema={"rid": "int64", "split": "string"},
            row_count=1000,
        ),
    )


@pytest.fixture
def manifest_with_addon(embedding_addon) -> Manifest:
    """Create a manifest with an embedding addon."""
    return Manifest(
        dataset="test/dataset",
        tables={
            "main": TableDescriptor(
                format="parquet",
                shards=[
                    ShardInfo(uri="s3://bucket/main.parquet", row_count=1000),
                ],
                schema={"rid": "int64", "text": "string"},
                row_count=1000,
            ),
        },
        addons={
            "embeddings:clip-vit-l14@openai": embedding_addon,
        },
    )


@pytest.fixture
def manifest_with_multiple_addons(embedding_addon, splits_addon) -> Manifest:
    """Create a manifest with multiple addons."""
    return Manifest(
        dataset="test/dataset",
        tables={
            "main": TableDescriptor(
                format="parquet",
                shards=[
                    ShardInfo(uri="s3://bucket/main.parquet", row_count=1000),
                ],
            ),
        },
        addons={
            "embeddings:clip-vit-l14@openai": embedding_addon,
            "splits:v1": splits_addon,
        },
    )


# Model tests


class TestAddonDescriptor:
    """Tests for AddonDescriptor."""

    def test_is_embedding(self, embedding_addon):
        """Test is_embedding property."""
        assert embedding_addon.is_embedding is True

    def test_is_not_embedding(self, splits_addon):
        """Test is_embedding returns False for non-embedding addon."""
        assert splits_addon.is_embedding is False

    def test_to_dict(self, embedding_addon):
        """Test serialization to dict."""
        d = embedding_addon.to_dict()

        assert d["kind"] == "embeddings"
        assert d["base_table"] == "main"
        assert d["key"]["type"] == "rid"
        assert d["key"]["column"] == "rid"
        assert "vectors" in d
        assert "params" in d
        assert d["params"]["dims"] == 768

    def test_to_dict_with_index(self, embedding_addon_with_index):
        """Test serialization includes index."""
        d = embedding_addon_with_index.to_dict()

        assert "index" in d
        assert d["index"]["kind"] == "faiss"
        assert d["index"]["meta"]["type"] == "HNSW"


class TestKeyMapping:
    """Tests for KeyMapping."""

    def test_to_dict(self):
        """Test serialization."""
        key = KeyMapping(type="rid", column="row_id")
        d = key.to_dict()

        assert d["type"] == "rid"
        assert d["column"] == "row_id"


class TestEmbeddingParams:
    """Tests for EmbeddingParams."""

    def test_to_dict(self):
        """Test serialization."""
        params = EmbeddingParams(
            provider="openai",
            model="text-embedding-3-large",
            dims=3072,
            metric="cosine",
            normalized=True,
            source_columns=["text", "title"],
        )
        d = params.to_dict()

        assert d["provider"] == "openai"
        assert d["model"] == "text-embedding-3-large"
        assert d["dims"] == 3072
        assert d["source_columns"] == ["text", "title"]


class TestIndexDescriptor:
    """Tests for IndexDescriptor."""

    def test_to_dict(self):
        """Test serialization."""
        index = IndexDescriptor(
            kind="faiss",
            uri="s3://bucket/index.faiss",
            byte_size=1024,
            meta={"type": "HNSW"},
        )
        d = index.to_dict()

        assert d["kind"] == "faiss"
        assert d["uri"] == "s3://bucket/index.faiss"
        assert d["byte_size"] == 1024
        assert d["meta"]["type"] == "HNSW"


# Manifest tests


class TestManifestAddons:
    """Tests for Manifest addon support."""

    def test_manifest_with_addons(self, manifest_with_addon):
        """Test manifest includes addons."""
        assert len(manifest_with_addon.addons) == 1
        assert "embeddings:clip-vit-l14@openai" in manifest_with_addon.addons

    def test_manifest_to_dict_includes_addons(self, manifest_with_addon):
        """Test manifest serialization includes addons."""
        d = manifest_with_addon.to_dict()

        assert "addons" in d
        assert "embeddings:clip-vit-l14@openai" in d["addons"]

    def test_manifest_from_dict_parses_addons(self, manifest_with_addon):
        """Test manifest deserialization parses addons."""
        d = manifest_with_addon.to_dict()
        restored = Manifest.from_dict(d)

        assert len(restored.addons) == 1
        addon = restored.addons["embeddings:clip-vit-l14@openai"]
        assert addon.kind == "embeddings"
        assert addon.params.dims == 768

    def test_version_hash_includes_addons(self, manifest_with_addon):
        """Test version hash changes with addons."""
        manifest_no_addon = Manifest(
            dataset="test/dataset",
            tables=manifest_with_addon.tables,
        )

        # Version should be different with addons
        assert manifest_with_addon.version_hash != manifest_no_addon.version_hash


# EmbeddingSpace tests


class TestEmbeddingSpace:
    """Tests for EmbeddingSpace class."""

    def test_creation(self, embedding_addon, manifest_with_addon):
        """Test EmbeddingSpace creation."""
        engine = Mock()
        settings = Settings()

        space = EmbeddingSpace(
            name="embeddings:clip-vit-l14@openai",
            descriptor=embedding_addon,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )

        assert space.name == "embeddings:clip-vit-l14@openai"
        assert space.dims == 768
        assert space.metric == "cosine"
        assert space.provider == "openai"
        assert space.model == "clip-vit-l14"

    def test_non_embedding_raises(self, splits_addon, manifest_with_addon):
        """Test creating EmbeddingSpace with non-embedding addon raises."""
        engine = Mock()
        settings = Settings()

        with pytest.raises(ValueError, match="not an embedding space"):
            EmbeddingSpace(
                name="splits:v1",
                descriptor=splits_addon,
                manifest=manifest_with_addon,
                settings=settings,
                engine=engine,
            )

    def test_has_index(self, embedding_addon, embedding_addon_with_index, manifest_with_addon):
        """Test has_index property."""
        engine = Mock()
        settings = Settings()

        # Without index
        space = EmbeddingSpace(
            name="test",
            descriptor=embedding_addon,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )
        assert space.has_index is False

        # With index
        space_with_index = EmbeddingSpace(
            name="test",
            descriptor=embedding_addon_with_index,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )
        assert space_with_index.has_index is True

    def test_info(self, embedding_addon, manifest_with_addon):
        """Test info() method."""
        engine = Mock()
        settings = Settings()

        space = EmbeddingSpace(
            name="embeddings:clip",
            descriptor=embedding_addon,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )

        info = space.info()

        assert info["name"] == "embeddings:clip"
        assert info["kind"] == "embeddings"
        assert info["params"]["dims"] == 768
        assert info["vectors"]["row_count"] == 1000

    def test_compute_space_id(self):
        """Test deterministic space ID computation."""
        # Same inputs should produce same ID
        id1 = EmbeddingSpace.compute_space_id(
            dataset_version="abc123",
            provider="openai",
            model="clip-vit-l14",
            dims=768,
            metric="cosine",
            normalized=True,
            source_columns=["image_path"],
        )

        id2 = EmbeddingSpace.compute_space_id(
            dataset_version="abc123",
            provider="openai",
            model="clip-vit-l14",
            dims=768,
            metric="cosine",
            normalized=True,
            source_columns=["image_path"],
        )

        assert id1 == id2

        # Different inputs should produce different ID
        id3 = EmbeddingSpace.compute_space_id(
            dataset_version="abc123",
            provider="openai",
            model="clip-vit-l14",
            dims=768,
            metric="euclidean",  # Changed
            normalized=True,
            source_columns=["image_path"],
        )

        assert id1 != id3


class TestEmbeddingSpaceSearch:
    """Tests for EmbeddingSpace search functionality."""

    def test_compute_distance_cosine(self, embedding_addon, manifest_with_addon):
        """Test cosine distance computation."""
        engine = Mock()
        settings = Settings()

        space = EmbeddingSpace(
            name="test",
            descriptor=embedding_addon,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )

        # Identical vectors should have distance 0
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        dist = space._compute_distance(a, b)
        assert abs(dist) < 1e-6

        # Orthogonal vectors should have distance 1
        c = np.array([0.0, 1.0, 0.0])
        dist = space._compute_distance(a, c)
        assert abs(dist - 1.0) < 1e-6

    def test_search_validation(self, embedding_addon, manifest_with_addon):
        """Test search validates query dimensions."""
        engine = Mock()
        settings = Settings()

        space = EmbeddingSpace(
            name="test",
            descriptor=embedding_addon,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )

        # Wrong dimensions should raise
        with pytest.raises(ValueError, match="must be shape"):
            space.search(np.zeros(100), k=10)


# VectorsTable tests


class TestVectorsTable:
    """Tests for VectorsTable class."""

    def test_vectors_table_properties(self, embedding_addon, manifest_with_addon):
        """Test VectorsTable properties."""
        engine = Mock()
        settings = Settings()

        space = EmbeddingSpace(
            name="test",
            descriptor=embedding_addon,
            manifest=manifest_with_addon,
            settings=settings,
            engine=engine,
        )

        vectors = space.vectors()

        assert vectors.row_count == 1000
        assert vectors.shard_count == 1
        assert vectors.key_column == "rid"
