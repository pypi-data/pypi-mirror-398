"""Manifest analysis for code generation.

Analyzes a manifest to determine:
- Which tables to scaffold
- Which bindings apply and their media types
- Recommended defaults for wrap_refs, format, columns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from warpdatasets.manifest.model import Manifest


@dataclass
class BindingInfo:
    """Information about a binding for code generation."""

    column: str
    artifact: str
    media_type: str
    ref_type: str


@dataclass
class TableAnalysis:
    """Analysis of a table for code generation."""

    name: str
    row_count: int | None
    column_count: int
    columns: list[str]
    bindings: list[BindingInfo]

    @property
    def has_bindings(self) -> bool:
        """Whether this table has any bindings."""
        return len(self.bindings) > 0

    @property
    def has_image_refs(self) -> bool:
        """Whether this table has image bindings."""
        return any(b.media_type == "image" for b in self.bindings)

    @property
    def has_audio_refs(self) -> bool:
        """Whether this table has audio bindings."""
        return any(b.media_type == "audio" for b in self.bindings)

    @property
    def ref_columns(self) -> list[str]:
        """Get list of columns that are ref columns."""
        return [b.column for b in self.bindings]


@dataclass
class ManifestAnalysis:
    """Complete analysis of a manifest for code generation."""

    dataset_id: str
    version: str | None
    tables: dict[str, TableAnalysis]
    has_artifacts: bool
    artifact_names: list[str]

    @property
    def main_table(self) -> TableAnalysis | None:
        """Get the main table analysis."""
        return self.tables.get("main")

    @property
    def has_bindings(self) -> bool:
        """Whether any table has bindings."""
        return any(t.has_bindings for t in self.tables.values())

    @property
    def recommended_format(self) -> str:
        """Recommend output format based on bindings."""
        # Dict mode is required for wrap_refs
        if self.has_bindings:
            return "dict"
        return "dict"  # Always dict for simplicity in v1

    @property
    def recommended_wrap_refs(self) -> bool:
        """Recommend wrap_refs based on bindings."""
        return self.has_bindings


def analyze_manifest(manifest: Manifest, version: str | None = None) -> ManifestAnalysis:
    """Analyze a manifest for code generation.

    Args:
        manifest: The manifest to analyze
        version: Optional version hash

    Returns:
        ManifestAnalysis with recommendations for code generation
    """
    tables = {}

    for table_name, table_desc in manifest.tables.items():
        # Get columns from schema
        columns = list(table_desc.schema.keys()) if table_desc.schema else []

        # Find bindings for this table
        bindings = []
        for binding in manifest.bindings:
            if binding.table == table_name:
                bindings.append(BindingInfo(
                    column=binding.column,
                    artifact=binding.artifact,
                    media_type=binding.media_type,
                    ref_type=binding.ref_type,
                ))

        tables[table_name] = TableAnalysis(
            name=table_name,
            row_count=table_desc.row_count,
            column_count=len(columns),
            columns=columns,
            bindings=bindings,
        )

    return ManifestAnalysis(
        dataset_id=manifest.dataset,
        version=version,
        tables=tables,
        has_artifacts=bool(manifest.artifacts),
        artifact_names=list(manifest.artifacts.keys()),
    )
