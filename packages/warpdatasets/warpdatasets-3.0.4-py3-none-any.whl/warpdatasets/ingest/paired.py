"""Paired data ingestor - handle image+mask, audio+transcript, etc.

For more flexible pairing scenarios than imagefolder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

from warpdatasets.ingest.base import (
    Ingestor,
    IngestPlan,
    ArtifactSpec,
    BindingSpec,
    MediaType,
    IdStrategy,
    compute_id,
)


@dataclass
class SourceSpec:
    """Specification for a source directory."""

    name: str
    source_dir: Path
    pattern: str | None = None  # glob pattern like "*.png" or None for all
    media_type: MediaType = "file"
    is_primary: bool = False  # Primary source determines the ID


@dataclass
class PairedIngestor(Ingestor):
    """Ingest paired data from multiple directories.

    Example: image + mask + metadata JSON

        ingestor = PairedIngestor(
            sources=[
                SourceSpec("images", Path("images"), "*.png", "image", is_primary=True),
                SourceSpec("masks", Path("masks"), "*.npy", "file"),
                SourceSpec("meta", Path("annotations"), "*.json", "file"),
            ],
            match_pattern="{id}",  # How to match files across sources
        )
    """

    sources: list[SourceSpec]
    match_pattern: str = "{id}"  # Pattern for matching files
    id_strategy: IdStrategy = "stem"

    @property
    def name(self) -> str:
        return "paired"

    def _get_primary(self) -> SourceSpec:
        """Get the primary source (determines IDs)."""
        for src in self.sources:
            if src.is_primary:
                return src
        return self.sources[0]  # Default to first

    def _find_files(self, source: SourceSpec) -> dict[str, Path]:
        """Find files in source and map by ID."""
        files = {}

        if source.pattern:
            paths = list(source.source_dir.glob(source.pattern))
        else:
            paths = [p for p in source.source_dir.iterdir() if p.is_file()]

        for path in paths:
            file_id = compute_id(path, source.source_dir, self.id_strategy)
            files[file_id] = path

        return files

    def _match_file(self, source: SourceSpec, primary_id: str, source_files: dict[str, Path]) -> str | None:
        """Find matching file in secondary source.

        Args:
            source: Source specification
            primary_id: ID from primary source
            source_files: Pre-scanned files from this source

        Returns:
            Relative path to matched file, or None
        """
        # Direct ID match
        if primary_id in source_files:
            path = source_files[primary_id]
            return str(path.relative_to(source.source_dir))

        # Pattern-based match
        expected = self.match_pattern.replace("{id}", primary_id)
        for file_id, path in source_files.items():
            if path.name.startswith(expected) or file_id == expected:
                return str(path.relative_to(source.source_dir))

        return None

    def plan(self) -> IngestPlan:
        """Scan sources and produce an ingest plan."""
        primary = self._get_primary()
        primary_files = self._find_files(primary)

        if not primary_files:
            raise ValueError(f"No files found in primary source {primary.source_dir}")

        # Pre-scan secondary sources
        secondary_files = {}
        for source in self.sources:
            if source != primary:
                secondary_files[source.name] = self._find_files(source)

        rows = []
        for file_id, primary_path in sorted(primary_files.items()):
            row: dict[str, Any] = {
                "id": file_id,
                f"{primary.name}_ref": str(primary_path.relative_to(primary.source_dir)),
            }

            # Match secondary sources
            for source in self.sources:
                if source != primary:
                    col_name = f"{source.name}_ref"
                    row[col_name] = self._match_file(
                        source, file_id, secondary_files[source.name]
                    )

            rows.append(row)

        # Build artifact specs
        artifacts = [
            ArtifactSpec(
                name=src.name,
                source_dir=src.source_dir,
                media_type=src.media_type,
            )
            for src in self.sources
        ]

        # Build binding specs
        bindings = [
            BindingSpec(
                table="main",
                column=f"{src.name}_ref",
                artifact=src.name,
                media_type=src.media_type,
                ref_type="file_path",
            )
            for src in self.sources
        ]

        return IngestPlan(
            table_data=rows,
            artifacts=artifacts,
            bindings=bindings,
            meta={
                "ingestor": self.name,
                "primary_source": primary.name,
                "sources": [s.name for s in self.sources],
            },
        )


def paired(
    dataset_id: str,
    *,
    primary: tuple[str, str | Path, str | None, MediaType],
    secondaries: list[tuple[str, str | Path, str | None, MediaType]] | None = None,
    match_pattern: str = "{id}",
    id_strategy: IdStrategy = "stem",
    workspace_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    progress: bool = True,
    dry_run: bool = False,
) -> IngestPlan | Path:
    """Ingest paired data from multiple directories.

    Args:
        dataset_id: Target dataset ID
        primary: Primary source (name, dir, pattern, media_type)
            e.g., ("images", "train_images", "*.png", "image")
        secondaries: List of secondary sources, each as (name, dir, pattern, media_type)
        match_pattern: Pattern for matching files (default: "{id}")
        id_strategy: ID strategy ("stem", "relative", "hash")
        workspace_root: Workspace root directory
        output_dir: Where to write parquet
        progress: Show progress output
        dry_run: Only return plan without executing

    Returns:
        IngestPlan if dry_run=True, else Path to manifest

    Example:
        >>> import warpdatasets as wd
        >>> wd.ingest.paired(
        ...     "local/segmentation",
        ...     primary=("images", "data/images", "*.png", "image"),
        ...     secondaries=[
        ...         ("masks", "data/masks", "*.npy", "file"),
        ...         ("meta", "data/annotations", "*.json", "file"),
        ...     ],
        ... )
    """
    sources = []

    # Primary source
    name, dir_path, pattern, media_type = primary
    sources.append(SourceSpec(
        name=name,
        source_dir=Path(dir_path).expanduser().resolve(),
        pattern=pattern,
        media_type=media_type,
        is_primary=True,
    ))

    # Secondary sources
    if secondaries:
        for name, dir_path, pattern, media_type in secondaries:
            sources.append(SourceSpec(
                name=name,
                source_dir=Path(dir_path).expanduser().resolve(),
                pattern=pattern,
                media_type=media_type,
            ))

    ingestor = PairedIngestor(
        sources=sources,
        match_pattern=match_pattern,
        id_strategy=id_strategy,
    )

    plan = ingestor.plan()

    if dry_run:
        return plan

    return ingestor.run(
        dataset_id=dataset_id,
        output_dir=Path(output_dir).expanduser() if output_dir else None,
        workspace_root=Path(workspace_root).expanduser() if workspace_root else None,
        progress=progress,
    )
