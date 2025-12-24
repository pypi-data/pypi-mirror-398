"""Base classes for data ingestors.

Ingestors convert raw data (image folders, CSV+files, etc.) into
warpdatasets format (parquet tables + artifacts + bindings).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal


# Simplified media types for CLI/API
MediaType = Literal["image", "audio", "video", "file"]

# Map simplified types to MIME type prefixes
MEDIA_TYPE_MAP = {
    "image": "image/*",
    "audio": "audio/*",
    "video": "video/*",
    "file": "application/octet-stream",
}


@dataclass
class ArtifactSpec:
    """Specification for an artifact to be created."""

    name: str
    source_dir: Path
    media_type: MediaType = "file"

    def to_mime_type(self) -> str:
        """Convert simplified media type to MIME type."""
        return MEDIA_TYPE_MAP.get(self.media_type, "application/octet-stream")


@dataclass
class BindingSpec:
    """Specification for a column->artifact binding."""

    table: str
    column: str
    artifact: str
    media_type: MediaType = "file"
    ref_type: str = "file_path"


@dataclass
class IngestPlan:
    """Plan produced by an ingestor before execution.

    Contains all the information needed to create a dataset:
    - Table data (as list of dicts or DataFrame)
    - Artifact specifications
    - Binding specifications
    - Metadata
    """

    table_data: list[dict[str, Any]]
    artifacts: list[ArtifactSpec]
    bindings: list[BindingSpec]
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return len(self.table_data)

    def summary(self) -> str:
        """Human-readable summary of the plan."""
        lines = [
            f"Rows: {self.row_count}",
            f"Artifacts: {', '.join(a.name for a in self.artifacts)}",
            f"Bindings: {len(self.bindings)}",
        ]
        return "\n".join(lines)


class Ingestor(ABC):
    """Base class for data ingestors.

    Ingestors follow a two-phase approach:
    1. plan() - Scan data and produce an IngestPlan
    2. run() - Execute the plan (write parquet, register dataset)

    This allows users to inspect what will happen before committing.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Ingestor name (e.g., 'imagefolder', 'paired')."""
        ...

    @abstractmethod
    def plan(self) -> IngestPlan:
        """Scan source data and produce an execution plan.

        Returns:
            IngestPlan with table data, artifacts, and bindings
        """
        ...

    def run(
        self,
        dataset_id: str,
        output_dir: Path | None = None,
        workspace_root: Path | None = None,
        progress: bool = True,
    ) -> Path:
        """Execute the ingest plan.

        Args:
            dataset_id: Target dataset ID (workspace/name)
            output_dir: Where to write parquet (default: workspace_root/data/...)
            workspace_root: Workspace root (default: from settings)
            progress: Show progress bar

        Returns:
            Path to the created manifest
        """
        import hashlib
        import json

        import pyarrow as pa
        import pyarrow.parquet as pq

        from warpdatasets.config import get_settings

        plan = self.plan()

        if workspace_root is None:
            settings = get_settings()
            workspace_root = Path(settings.workspace_root) if settings.workspace_root else Path.cwd()

        workspace_root = Path(workspace_root)

        # Determine output directory for parquet
        if output_dir is None:
            workspace, name = dataset_id.split("/", 1)
            output_dir = workspace_root / "data" / workspace / name

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write parquet
        parquet_path = output_dir / "main.parquet"

        if progress:
            print(f"Writing {plan.row_count} rows to {parquet_path}")

        table = pa.Table.from_pylist(plan.table_data)
        pq.write_table(table, parquet_path)

        # Build manifest
        manifest = {
            "dataset": dataset_id,
            "tables": {},
            "artifacts": {},
            "bindings": [],
            "meta": plan.meta,
        }

        # Add main table
        try:
            rel_path = parquet_path.resolve().relative_to(workspace_root.resolve())
            uri = f"local://{rel_path}"
        except ValueError:
            uri = f"file://{parquet_path.resolve()}"

        pf = pq.ParquetFile(parquet_path)
        manifest["tables"]["main"] = {
            "format": "parquet",
            "shards": [{"uri": uri, "byte_size": parquet_path.stat().st_size}],
            "schema": {f.name: str(f.type) for f in pf.schema_arrow},
            "row_count": pf.metadata.num_rows,
        }

        # Add artifacts
        for spec in plan.artifacts:
            try:
                rel_path = spec.source_dir.resolve().relative_to(workspace_root.resolve())
                uri = f"local://{rel_path}"
            except ValueError:
                uri = f"file://{spec.source_dir.resolve()}"

            manifest["artifacts"][spec.name] = {
                "kind": "directory",
                "shards": [{"uri": uri}],
            }

        # Add bindings (use simplified media types: image, audio, video, file)
        for binding in plan.bindings:
            manifest["bindings"].append({
                "table": binding.table,
                "column": binding.column,
                "artifact": binding.artifact,
                "ref_type": binding.ref_type,
                "media_type": binding.media_type,  # Use simplified type directly
            })

        # Compute version hash
        hasher = hashlib.sha256()
        hasher.update(str(parquet_path).encode())
        hasher.update(str(parquet_path.stat().st_size).encode())
        with open(parquet_path, "rb") as f:
            hasher.update(f.read(4096))
        version = hasher.hexdigest()[:12]

        # Write manifest
        workspace, name = dataset_id.split("/", 1)
        manifest_dir = workspace_root / "manifests" / workspace / name
        manifest_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = manifest_dir / f"{version}.json"
        latest_path = manifest_dir / "latest.json"

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        with open(latest_path, "w") as f:
            json.dump({"version": version}, f)

        if progress:
            print(f"Registered: {dataset_id}")
            print(f"Version: {version}")
            print(f"Rows: {plan.row_count}")
            print(f"Manifest: {manifest_path}")

        return manifest_path


# ID generation strategies
IdStrategy = Literal["stem", "relative", "hash"]


def compute_id(path: Path, base_dir: Path, strategy: IdStrategy = "stem") -> str:
    """Compute a stable ID for a file.

    Args:
        path: File path
        base_dir: Base directory for relative paths
        strategy: How to compute the ID
            - "stem": filename without extension (e.g., "image001")
            - "relative": relative path from base (e.g., "train/cat/001")
            - "hash": SHA256 hash of relative path

    Returns:
        Stable string ID
    """
    if strategy == "stem":
        return path.stem
    elif strategy == "relative":
        rel = path.relative_to(base_dir)
        return str(rel.with_suffix(""))
    elif strategy == "hash":
        import hashlib
        rel = str(path.relative_to(base_dir))
        return hashlib.sha256(rel.encode()).hexdigest()[:16]
    else:
        raise ValueError(f"Unknown ID strategy: {strategy}")


# Label strategies
LabelStrategy = Literal["from-parent", "none"]


def compute_label(path: Path, base_dir: Path, strategy: LabelStrategy) -> str | None:
    """Compute a label for a file.

    Args:
        path: File path
        base_dir: Base directory
        strategy: How to compute the label
            - "from-parent": use parent directory name
            - "none": no label

    Returns:
        Label string or None
    """
    if strategy == "none":
        return None
    elif strategy == "from-parent":
        # Get the immediate parent directory name relative to base
        rel = path.relative_to(base_dir)
        if len(rel.parts) > 1:
            return rel.parts[0]
        return None
    else:
        raise ValueError(f"Unknown label strategy: {strategy}")
