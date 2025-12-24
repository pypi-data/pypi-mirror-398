"""Register local dataset command.

Creates a local manifest from parquet files and optional artifact directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DATASET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$")


@dataclass
class TableSpec:
    """Specification for a table to register."""

    name: str
    shard_paths: list[Path]


@dataclass
class ArtifactSpec:
    """Specification for an artifact to register."""

    name: str
    directory: Path
    media_type: str = "file"


def parse_table_arg(arg: str) -> TableSpec:
    """Parse a table argument: name=path/to/shards/*.parquet

    Args:
        arg: Table specification string

    Returns:
        TableSpec with name and resolved shard paths

    Raises:
        ValueError: If format is invalid
    """
    if "=" not in arg:
        raise ValueError(f"Invalid table format: {arg}. Expected name=path/*.parquet")

    name, pattern = arg.split("=", 1)
    name = name.strip()
    pattern = pattern.strip()

    if not name:
        raise ValueError("Table name cannot be empty")

    # Expand glob pattern
    path = Path(pattern)
    if "*" in pattern:
        base = Path(pattern).parent
        glob_pattern = Path(pattern).name
        shard_paths = sorted(base.glob(glob_pattern))
    elif path.is_dir():
        # Directory: find all parquet files
        shard_paths = sorted(path.glob("*.parquet"))
    elif path.exists():
        # Single file
        shard_paths = [path]
    else:
        raise ValueError(f"No files found matching: {pattern}")

    if not shard_paths:
        raise ValueError(f"No parquet files found matching: {pattern}")

    return TableSpec(name=name, shard_paths=shard_paths)


def parse_artifact_arg(arg: str) -> ArtifactSpec:
    """Parse an artifact argument: name=path/to/directory[:media_type]

    Args:
        arg: Artifact specification string

    Returns:
        ArtifactSpec with name, directory, and media type

    Raises:
        ValueError: If format is invalid
    """
    if "=" not in arg:
        raise ValueError(f"Invalid artifact format: {arg}. Expected name=path[:media_type]")

    name, rest = arg.split("=", 1)
    name = name.strip()

    # Check for media type suffix
    if ":" in rest:
        path_str, media_type = rest.rsplit(":", 1)
    else:
        path_str = rest
        media_type = "file"

    path = Path(path_str.strip())
    if not path.is_dir():
        raise ValueError(f"Artifact path must be a directory: {path}")

    return ArtifactSpec(name=name, directory=path, media_type=media_type)


def compute_content_hash(shard_paths: list[Path]) -> str:
    """Compute a content-based hash from shard files.

    Args:
        shard_paths: Paths to shard files

    Returns:
        Short hash string (first 12 characters of SHA-256)
    """
    hasher = hashlib.sha256()

    for path in sorted(shard_paths):
        # Include file path and size in hash
        hasher.update(str(path).encode())
        hasher.update(str(path.stat().st_size).encode())

        # Read first 4KB of content for hash
        with open(path, "rb") as f:
            hasher.update(f.read(4096))

    return hasher.hexdigest()[:12]


def build_local_manifest(
    dataset_id: str,
    tables: list[TableSpec],
    artifacts: list[ArtifactSpec],
    workspace_root: Path,
) -> dict:
    """Build a manifest for local registration.

    Uses local:// URIs relative to workspace_root.

    Args:
        dataset_id: Dataset identifier (workspace/name)
        tables: Table specifications
        artifacts: Artifact specifications
        workspace_root: Root directory for local:// resolution

    Returns:
        Manifest dict
    """
    import pyarrow.parquet as pq

    manifest = {
        "dataset": dataset_id,
        "tables": {},
        "artifacts": {},
        "bindings": [],
        "meta": {},
    }

    # Build tables
    for table_spec in tables:
        shards = []
        row_count = 0
        schema = None

        for i, shard_path in enumerate(table_spec.shard_paths):
            # Convert to local:// URI
            try:
                rel_path = shard_path.resolve().relative_to(workspace_root.resolve())
                uri = f"local://{rel_path}"
            except ValueError:
                # Path is outside workspace, use absolute path
                uri = f"file://{shard_path.resolve()}"

            size = shard_path.stat().st_size
            shards.append({
                "uri": uri,
                "byte_size": size,
            })

            # Get metadata from parquet
            pf = pq.ParquetFile(shard_path)
            row_count += pf.metadata.num_rows

            if schema is None:
                schema = {f.name: str(f.type) for f in pf.schema_arrow}

        manifest["tables"][table_spec.name] = {
            "format": "parquet",
            "shards": shards,
            "schema": schema,
            "row_count": row_count,
        }

    # Build artifacts (directory type for local)
    for artifact_spec in artifacts:
        try:
            rel_path = artifact_spec.directory.resolve().relative_to(workspace_root.resolve())
            uri = f"local://{rel_path}"
        except ValueError:
            uri = f"file://{artifact_spec.directory.resolve()}"

        manifest["artifacts"][artifact_spec.name] = {
            "kind": "directory",
            "shards": [{"uri": uri}],
        }

        # Add binding if main table exists
        if "main" in manifest["tables"]:
            manifest["bindings"].append({
                "table": "main",
                "column": artifact_spec.name,
                "artifact": artifact_spec.name,
                "ref_type": "file_path",
                "media_type": artifact_spec.media_type,
            })

    return manifest


def run(args: argparse.Namespace) -> int:
    """Run the register command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code (0 for success)
    """
    from warpdatasets.config.settings import get_settings

    settings = get_settings()

    # Validate dataset ID
    dataset_id = args.dataset
    if not DATASET_ID_PATTERN.match(dataset_id):
        print(f"Error: Dataset ID must be in 'workspace/name' format: {dataset_id}", file=sys.stderr)
        return 1

    # Parse tables
    tables = []
    if args.table:
        for table_arg in args.table:
            try:
                tables.append(parse_table_arg(table_arg))
            except ValueError as e:
                print(f"Error parsing table: {e}", file=sys.stderr)
                return 1

    if not tables:
        print("Error: At least one table is required (use --table)", file=sys.stderr)
        return 1

    # Ensure main table exists
    if not any(t.name == "main" for t in tables):
        print("Error: A 'main' table is required", file=sys.stderr)
        return 1

    # Parse artifacts
    artifacts = []
    if args.artifact:
        for artifact_arg in args.artifact:
            try:
                artifacts.append(parse_artifact_arg(artifact_arg))
            except ValueError as e:
                print(f"Error parsing artifact: {e}", file=sys.stderr)
                return 1

    # Determine workspace root
    workspace_root = settings.workspace_root
    if args.workspace_root:
        workspace_root = Path(args.workspace_root)

    # Build manifest
    manifest = build_local_manifest(
        dataset_id=dataset_id,
        tables=tables,
        artifacts=artifacts,
        workspace_root=workspace_root,
    )

    # Compute version hash
    all_shard_paths = []
    for table_spec in tables:
        all_shard_paths.extend(table_spec.shard_paths)
    version = compute_content_hash(all_shard_paths)

    # Determine manifest path
    workspace, name = dataset_id.split("/")
    manifest_dir = workspace_root / "manifests" / workspace / name
    manifest_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = manifest_dir / f"{version}.json"
    latest_path = manifest_dir / "latest.json"

    # Check if already exists
    if manifest_path.exists() and not args.force:
        print(f"Manifest already exists: {manifest_path}")
        print("Use --force to overwrite")
        return 0

    # Write manifest
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Write latest pointer
    with open(latest_path, "w") as f:
        json.dump({"version": version}, f)

    # Summary
    main_table = manifest["tables"]["main"]
    print(f"Registered: {dataset_id}")
    print(f"Version: {version}")
    print(f"Rows: {main_table['row_count']}")
    print(f"Tables: {len(manifest['tables'])}")
    print(f"Artifacts: {len(manifest['artifacts'])}")
    print(f"Manifest: {manifest_path}")

    return 0
