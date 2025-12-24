"""Core generator for dataset loaders.

Generates runnable Python files from manifests.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from warpdatasets.tools.initgen.analyze import ManifestAnalysis, analyze_manifest
from warpdatasets.tools.initgen.naming import dataset_id_to_filename, dataset_id_to_module_name
from warpdatasets.tools.initgen.templates import (
    LOADER_TEMPLATE,
    IMAGE_DECODE_HELPER,
    AUDIO_DECODE_HELPER,
    FILE_DECODE_HELPER,
)

if TYPE_CHECKING:
    from warpdatasets.manifest.model import Manifest


class LoaderGenerator:
    """Generates Python loader code from manifests."""

    def __init__(
        self,
        manifest: Manifest,
        version: str | None = None,
        table: str = "main",
        mode: str = "auto",
        prefetch: str = "auto",
        include_refs: bool | None = None,
        columns: list[str] | None = None,
    ):
        """Initialize the generator.

        Args:
            manifest: Manifest to generate from
            version: Version hash
            table: Table to scaffold against
            mode: Default access mode
            prefetch: Default prefetch mode
            include_refs: Whether to include ref helpers (auto if None)
            columns: Specific columns to include
        """
        self.manifest = manifest
        self.version = version
        self.table = table
        self.mode = mode
        self.prefetch = prefetch
        self.columns = columns

        # Analyze manifest
        self.analysis = analyze_manifest(manifest, version)

        # Auto-detect include_refs
        if include_refs is None:
            table_analysis = self.analysis.tables.get(table)
            self.include_refs = table_analysis.has_bindings if table_analysis else False
        else:
            self.include_refs = include_refs

    def generate(self) -> str:
        """Generate the loader code.

        Returns:
            Python source code as a string
        """
        # Get table analysis
        table_analysis = self.analysis.tables.get(self.table)

        # Generate helpers if needed
        helpers = self._generate_helpers(table_analysis) if self.include_refs else ""

        # Determine wrap_refs
        wrap_refs = "True" if self.include_refs else "False"

        # Generate filename and module name
        filename = dataset_id_to_filename(self.manifest.dataset)
        module_name = dataset_id_to_module_name(self.manifest.dataset)

        # Format the template
        code = LOADER_TEMPLATE.format(
            dataset_id=self.manifest.dataset,
            default_table=self.table,
            default_mode=self.mode,
            default_prefetch=self.prefetch,
            wrap_refs=wrap_refs,
            helpers=helpers,
            filename=filename,
            module_name=module_name,
        )

        return code

    def _generate_helpers(self, table_analysis) -> str:
        """Generate helper functions for ref columns.

        Args:
            table_analysis: TableAnalysis for the target table

        Returns:
            Helper function code
        """
        if not table_analysis or not table_analysis.bindings:
            return ""

        helpers = []

        for binding in table_analysis.bindings:
            if binding.media_type == "image":
                helpers.append(IMAGE_DECODE_HELPER.format(column=binding.column))
            elif binding.media_type == "audio":
                helpers.append(AUDIO_DECODE_HELPER.format(column=binding.column))
            elif binding.media_type == "file":
                helpers.append(FILE_DECODE_HELPER.format(column=binding.column))

        return "\n".join(helpers)

    def write(self, output_path: Path | str | None = None, force: bool = False) -> Path:
        """Write the generated code to a file.

        Args:
            output_path: Output file path (auto-generated if None)
            force: Overwrite existing file

        Returns:
            Path to the written file

        Raises:
            FileExistsError: If file exists and force is False
        """
        if output_path is None:
            output_path = Path(dataset_id_to_filename(self.manifest.dataset))
        else:
            output_path = Path(output_path)

        if output_path.exists() and not force:
            raise FileExistsError(
                f"File already exists: {output_path}. Use --force to overwrite."
            )

        code = self.generate()
        output_path.write_text(code)

        return output_path


def generate_loader(
    manifest: Manifest,
    version: str | None = None,
    table: str = "main",
    mode: str = "auto",
    prefetch: str = "auto",
    include_refs: bool | None = None,
    columns: list[str] | None = None,
) -> str:
    """Generate a loader for a manifest.

    Args:
        manifest: Manifest to generate from
        version: Version hash
        table: Table to scaffold against
        mode: Default access mode
        prefetch: Default prefetch mode
        include_refs: Whether to include ref helpers (auto if None)
        columns: Specific columns to include

    Returns:
        Python source code as a string
    """
    generator = LoaderGenerator(
        manifest=manifest,
        version=version,
        table=table,
        mode=mode,
        prefetch=prefetch,
        include_refs=include_refs,
        columns=columns,
    )
    return generator.generate()
