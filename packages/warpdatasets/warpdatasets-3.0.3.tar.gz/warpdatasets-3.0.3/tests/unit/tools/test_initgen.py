"""Tests for init generator."""

import pytest

from warpdatasets.tools.initgen import (
    ManifestAnalysis,
    TableAnalysis,
    BindingInfo,
    analyze_manifest,
    dataset_id_to_filename,
    dataset_id_to_module_name,
    column_to_function_name,
    LoaderGenerator,
    generate_loader,
)
from warpdatasets.manifest.model import (
    Manifest,
    TableDescriptor,
    ShardInfo,
    ArtifactDescriptor,
    Binding,
)


# Fixtures


@pytest.fixture
def simple_manifest() -> Manifest:
    """Create a simple manifest without bindings."""
    return Manifest(
        dataset="test/simple",
        tables={
            "main": TableDescriptor(
                format="parquet",
                shards=[
                    ShardInfo(
                        uri="s3://bucket/data/shard-0.parquet",
                        row_count=1000,
                    ),
                ],
                schema={"id": "int64", "name": "string"},
                row_count=1000,
            ),
        },
    )


@pytest.fixture
def manifest_with_bindings() -> Manifest:
    """Create a manifest with image bindings."""
    return Manifest(
        dataset="vision/images",
        tables={
            "main": TableDescriptor(
                format="parquet",
                shards=[
                    ShardInfo(
                        uri="s3://bucket/data/shard-0.parquet",
                        row_count=1000,
                    ),
                ],
                schema={"id": "int64", "image_ref": "string"},
                row_count=1000,
            ),
            "captions": TableDescriptor(
                format="parquet",
                shards=[
                    ShardInfo(
                        uri="s3://bucket/data/captions-0.parquet",
                        row_count=500,
                    ),
                ],
                schema={"id": "int64", "caption": "string"},
                row_count=500,
            ),
        },
        artifacts={
            "images": ArtifactDescriptor(
                kind="tar_shards",
                shards=[
                    ShardInfo(
                        uri="s3://bucket/artifacts/images.tar",
                    ),
                ],
            ),
        },
        bindings=[
            Binding(
                table="main",
                column="image_ref",
                artifact="images",
                media_type="image",
                ref_type="member_path",
            ),
        ],
    )


# Naming tests


class TestNaming:
    """Tests for naming utilities."""

    def test_dataset_id_to_filename_simple(self):
        """Test simple dataset ID to filename."""
        assert dataset_id_to_filename("test/animals") == "test_animals_loader.py"

    def test_dataset_id_to_filename_deep(self):
        """Test deep dataset ID to filename."""
        assert dataset_id_to_filename("org/project/dataset") == "org_project_dataset_loader.py"

    def test_dataset_id_to_filename_special_chars(self):
        """Test dataset ID with special characters."""
        assert dataset_id_to_filename("my-org/my-dataset") == "my_org_my_dataset_loader.py"

    def test_dataset_id_to_module_name(self):
        """Test dataset ID to module name."""
        assert dataset_id_to_module_name("test/animals") == "test_animals_loader"

    def test_dataset_id_to_module_name_special(self):
        """Test dataset ID with special characters to module name."""
        assert dataset_id_to_module_name("my-org/my-dataset") == "my_org_my_dataset_loader"

    def test_column_to_function_name(self):
        """Test column name to function name."""
        assert column_to_function_name("image_path") == "decode_image_path"

    def test_column_to_function_name_special(self):
        """Test column name with special characters."""
        assert column_to_function_name("image-ref") == "decode_image_ref"


# Analysis tests


class TestAnalyzeManifest:
    """Tests for manifest analysis."""

    def test_simple_manifest(self, simple_manifest):
        """Test analyzing a simple manifest."""
        analysis = analyze_manifest(simple_manifest)

        assert analysis.dataset_id == "test/simple"
        assert "main" in analysis.tables
        assert analysis.tables["main"].name == "main"
        assert analysis.tables["main"].row_count == 1000
        assert analysis.tables["main"].column_count == 2
        assert not analysis.tables["main"].has_bindings
        assert analysis.tables["main"].bindings == []

    def test_manifest_with_bindings(self, manifest_with_bindings):
        """Test analyzing a manifest with bindings."""
        analysis = analyze_manifest(manifest_with_bindings)

        assert analysis.dataset_id == "vision/images"
        assert "main" in analysis.tables
        assert "captions" in analysis.tables

        # Main table has bindings
        main_table = analysis.tables["main"]
        assert main_table.has_bindings
        assert len(main_table.bindings) == 1
        assert main_table.ref_columns == ["image_ref"]

        # Check binding info
        binding = main_table.bindings[0]
        assert binding.column == "image_ref"
        assert binding.artifact == "images"
        assert binding.media_type == "image"

        # Captions table has no bindings
        captions_table = analysis.tables["captions"]
        assert not captions_table.has_bindings
        assert captions_table.bindings == []

    def test_analysis_with_version(self, simple_manifest):
        """Test analysis includes version when provided."""
        analysis = analyze_manifest(simple_manifest, version="abc123")
        assert analysis.version == "abc123"


# Generator tests


class TestLoaderGenerator:
    """Tests for loader generator."""

    def test_generate_simple(self, simple_manifest):
        """Test generating code for simple manifest."""
        generator = LoaderGenerator(manifest=simple_manifest)
        code = generator.generate()

        # Check imports
        assert "import warpdatasets as wd" in code

        # Check dataset config
        assert 'DATASET_ID = "test/simple"' in code
        assert 'DEFAULT_TABLE = "main"' in code

        # Check functions exist
        assert "def get_dataset(" in code
        assert "def stream_batches(" in code

        # No decode helpers for simple manifest
        assert "def decode_" not in code

        # Code should be valid Python
        compile(code, "<test>", "exec")

    def test_generate_with_bindings(self, manifest_with_bindings):
        """Test generating code for manifest with bindings."""
        generator = LoaderGenerator(manifest=manifest_with_bindings)
        code = generator.generate()

        # Check dataset config
        assert 'DATASET_ID = "vision/images"' in code

        # Should have decode_images helper with image_ref as default key
        assert "def decode_images(" in code
        assert 'key: str = "image_ref"' in code

        # Code should be valid Python
        compile(code, "<test>", "exec")

    def test_generate_with_mode(self, simple_manifest):
        """Test generating code with specific mode."""
        generator = LoaderGenerator(manifest=simple_manifest, mode="local")
        code = generator.generate()

        assert 'DEFAULT_MODE = "local"' in code

    def test_generate_with_prefetch(self, simple_manifest):
        """Test generating code with specific prefetch."""
        generator = LoaderGenerator(manifest=simple_manifest, prefetch="aggressive")
        code = generator.generate()

        assert 'DEFAULT_PREFETCH = "aggressive"' in code

    def test_generate_no_refs(self, manifest_with_bindings):
        """Test generating code without ref helpers."""
        generator = LoaderGenerator(manifest=manifest_with_bindings, include_refs=False)
        code = generator.generate()

        # Should not have decode helpers
        assert "def decode_images(" not in code
        assert "wrap_refs: bool = False" in code

    def test_generate_for_different_table(self, manifest_with_bindings):
        """Test generating code for non-main table."""
        generator = LoaderGenerator(manifest=manifest_with_bindings, table="captions")
        code = generator.generate()

        assert 'DEFAULT_TABLE = "captions"' in code

        # Captions table has no bindings, so no decode helpers
        assert "def decode_" not in code


class TestGenerateLoader:
    """Tests for generate_loader convenience function."""

    def test_generate_loader_simple(self, simple_manifest):
        """Test generate_loader function."""
        code = generate_loader(simple_manifest)

        assert 'DATASET_ID = "test/simple"' in code
        assert "def get_dataset(" in code
        compile(code, "<test>", "exec")

    def test_generate_loader_with_options(self, simple_manifest):
        """Test generate_loader with options."""
        code = generate_loader(
            simple_manifest,
            mode="hybrid",
            prefetch="auto",
        )

        assert 'DEFAULT_MODE = "hybrid"' in code
        assert 'DEFAULT_PREFETCH = "auto"' in code


class TestTableAnalysis:
    """Tests for TableAnalysis dataclass."""

    def test_table_analysis_no_bindings(self):
        """Test TableAnalysis without bindings."""
        analysis = TableAnalysis(
            name="main",
            row_count=10000,
            column_count=5,
            columns=["id", "name", "value", "created", "updated"],
            bindings=[],
        )

        assert analysis.name == "main"
        assert analysis.row_count == 10000
        assert analysis.column_count == 5
        assert not analysis.has_bindings
        assert analysis.ref_columns == []

    def test_table_analysis_with_bindings(self):
        """Test TableAnalysis with bindings."""
        bindings = [
            BindingInfo(column="image", artifact="images", media_type="image", ref_type="member_path"),
            BindingInfo(column="audio", artifact="sounds", media_type="audio", ref_type="member_path"),
        ]

        analysis = TableAnalysis(
            name="main",
            row_count=10000,
            column_count=5,
            columns=["id", "image", "audio", "label", "created"],
            bindings=bindings,
        )

        assert analysis.has_bindings
        assert analysis.ref_columns == ["image", "audio"]


class TestBindingInfo:
    """Tests for BindingInfo dataclass."""

    def test_binding_info_basic(self):
        """Test basic BindingInfo."""
        info = BindingInfo(
            column="image_path",
            artifact="images",
            media_type="image",
            ref_type="member_path",
        )

        assert info.column == "image_path"
        assert info.artifact == "images"
        assert info.media_type == "image"
        assert info.ref_type == "member_path"

    def test_binding_info_with_file_path(self):
        """Test BindingInfo with file_path ref_type."""
        info = BindingInfo(
            column="file_path",
            artifact="files",
            media_type="file",
            ref_type="file_path",
        )

        assert info.ref_type == "file_path"
