"""CSV+files ingestor - convert CSV with file paths to refs.

Handles datasets where metadata is in CSV and files are referenced by path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from warpdatasets.ingest.base import (
    Ingestor,
    IngestPlan,
    ArtifactSpec,
    BindingSpec,
    MediaType,
)


@dataclass
class FileColumnSpec:
    """Specification for a CSV column containing file paths."""

    column: str  # CSV column name
    artifact_name: str  # Name for the artifact
    base_dir: Path  # Base directory for resolving paths
    media_type: MediaType = "file"
    ref_column: str | None = None  # Output column name (default: {column}_ref)


@dataclass
class CSVFilesIngestor(Ingestor):
    """Ingest CSV with file path columns.

    Example: CSV with image_path, mask_path columns

        ingestor = CSVFilesIngestor(
            csv_path=Path("metadata.csv"),
            file_columns=[
                FileColumnSpec("image_path", "images", Path("images"), "image"),
                FileColumnSpec("mask_path", "masks", Path("masks"), "file"),
            ],
        )
    """

    csv_path: Path
    file_columns: list[FileColumnSpec]
    id_column: str | None = None  # Column to use as ID (default: auto-generate)
    keep_columns: list[str] | None = None  # Columns to keep (default: all)
    drop_columns: list[str] | None = None  # Columns to drop

    @property
    def name(self) -> str:
        return "csv_files"

    def _load_csv(self) -> list[dict[str, Any]]:
        """Load CSV file as list of dicts."""
        import csv

        rows = []
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

    def _process_row(self, row: dict[str, Any], row_idx: int) -> dict[str, Any]:
        """Process a single row, converting file paths to refs."""
        result: dict[str, Any] = {}

        # Handle ID
        if self.id_column and self.id_column in row:
            result["id"] = row[self.id_column]
        else:
            result["id"] = str(row_idx)

        # Copy other columns
        for key, value in row.items():
            # Skip file path columns (will be converted to refs)
            file_col_names = {fc.column for fc in self.file_columns}
            if key in file_col_names:
                continue

            # Skip if not in keep list
            if self.keep_columns and key not in self.keep_columns and key != self.id_column:
                continue

            # Skip if in drop list
            if self.drop_columns and key in self.drop_columns:
                continue

            result[key] = value

        # Convert file paths to refs
        for fc in self.file_columns:
            ref_col = fc.ref_column or f"{fc.artifact_name}_ref"
            path_value = row.get(fc.column)

            if path_value:
                # Make path relative to base_dir
                full_path = fc.base_dir / path_value
                if full_path.exists():
                    # Store relative path from artifact root
                    result[ref_col] = path_value
                else:
                    # Try as already-relative path
                    result[ref_col] = path_value
            else:
                result[ref_col] = None

        return result

    def plan(self) -> IngestPlan:
        """Load CSV and produce an ingest plan."""
        csv_rows = self._load_csv()

        if not csv_rows:
            raise ValueError(f"No rows found in {self.csv_path}")

        rows = [
            self._process_row(row, idx)
            for idx, row in enumerate(csv_rows)
        ]

        # Build artifact specs (deduplicate by name)
        seen_artifacts = set()
        artifacts = []
        for fc in self.file_columns:
            if fc.artifact_name not in seen_artifacts:
                artifacts.append(ArtifactSpec(
                    name=fc.artifact_name,
                    source_dir=fc.base_dir,
                    media_type=fc.media_type,
                ))
                seen_artifacts.add(fc.artifact_name)

        # Build binding specs
        bindings = [
            BindingSpec(
                table="main",
                column=fc.ref_column or f"{fc.artifact_name}_ref",
                artifact=fc.artifact_name,
                media_type=fc.media_type,
                ref_type="file_path",
            )
            for fc in self.file_columns
        ]

        return IngestPlan(
            table_data=rows,
            artifacts=artifacts,
            bindings=bindings,
            meta={
                "ingestor": self.name,
                "csv_path": str(self.csv_path),
            },
        )


def csv_files(
    dataset_id: str,
    csv_path: str | Path,
    file_columns: dict[str, tuple[str, str | Path, MediaType]],
    *,
    id_column: str | None = None,
    keep_columns: list[str] | None = None,
    drop_columns: list[str] | None = None,
    workspace_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    progress: bool = True,
    dry_run: bool = False,
) -> IngestPlan | Path:
    """Ingest a CSV file with file path columns.

    Args:
        dataset_id: Target dataset ID
        csv_path: Path to CSV file
        file_columns: Dict of csv_column -> (artifact_name, base_dir, media_type)
            e.g., {"image_path": ("images", "data/images", "image")}
        id_column: Column to use as ID (default: auto-generate)
        keep_columns: Columns to keep (default: all)
        drop_columns: Columns to drop
        workspace_root: Workspace root directory
        output_dir: Where to write parquet
        progress: Show progress output
        dry_run: Only return plan without executing

    Returns:
        IngestPlan if dry_run=True, else Path to manifest

    Example:
        >>> import warpdatasets as wd
        >>> wd.ingest.csv_files(
        ...     "local/my_dataset",
        ...     "metadata.csv",
        ...     file_columns={
        ...         "image_path": ("images", "data/images", "image"),
        ...         "mask_path": ("masks", "data/masks", "file"),
        ...     },
        ...     id_column="sample_id",
        ... )
    """
    csv_path = Path(csv_path).expanduser().resolve()

    file_specs = [
        FileColumnSpec(
            column=col,
            artifact_name=artifact_name,
            base_dir=Path(base_dir).expanduser().resolve(),
            media_type=media_type,
        )
        for col, (artifact_name, base_dir, media_type) in file_columns.items()
    ]

    ingestor = CSVFilesIngestor(
        csv_path=csv_path,
        file_columns=file_specs,
        id_column=id_column,
        keep_columns=keep_columns,
        drop_columns=drop_columns,
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
