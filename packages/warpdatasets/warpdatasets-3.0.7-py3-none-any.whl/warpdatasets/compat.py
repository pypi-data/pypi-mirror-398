"""Compatibility layer for old warpdata API.

This module provides backward-compatible functions matching the old warpdata API.
Just change your import from `import warpdata as wd` to:

    from warpdatasets.compat import wd
    # or
    from warpdatasets import compat as wd

Then all your old code should work:
    wd.load("vision/mnist")
    wd.head("vision/mnist", n=5)
    wd.list_datasets()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from warpdatasets.api.dataset import dataset, from_manifest
from warpdatasets.config.settings import get_settings

# Shared DuckDB connection for compat layer
_conn: "duckdb.DuckDBPyConnection | None" = None


def _get_conn() -> "duckdb.DuckDBPyConnection":
    """Get or create shared DuckDB connection."""
    global _conn
    if _conn is None:
        _conn = duckdb.connect(":memory:")
    return _conn


def list_datasets() -> list[dict[str, Any]]:
    """List all available datasets.

    Returns:
        List of dicts with workspace, name, latest_version, etc.
    """
    settings = get_settings()
    manifest_dir = settings.workspace_root / "manifests"

    datasets = []
    if not manifest_dir.exists():
        return datasets

    for workspace_path in sorted(manifest_dir.iterdir()):
        if not workspace_path.is_dir():
            continue
        workspace = workspace_path.name

        for dataset_path in sorted(workspace_path.iterdir()):
            if not dataset_path.is_dir():
                continue
            name = dataset_path.name

            # Read latest.json
            latest_path = dataset_path / "latest.json"
            if not latest_path.exists():
                continue

            import json
            try:
                latest = json.loads(latest_path.read_text())
                version = latest.get("version", "unknown")

                # Get timestamps from file
                stat = latest_path.stat()
                from datetime import datetime
                mtime = datetime.fromtimestamp(stat.st_mtime)

                datasets.append({
                    "workspace": workspace,
                    "name": name,
                    "latest_version": version,
                    "created_at": mtime,
                    "updated_at": mtime,
                })
            except Exception:
                continue

    return datasets


def load(source: str) -> "duckdb.DuckDBPyRelation":
    """Load dataset as DuckDB relation (lazy).

    Args:
        source: Dataset ID in "workspace/name" format

    Returns:
        DuckDB relation for lazy querying
    """
    ds = dataset(source)
    tbl = ds.table("main")

    # Get the shared DuckDB connection
    conn = _get_conn()

    # Register all parquet shards
    uris = []
    for shard in tbl.descriptor.shards:
        if shard.uri:
            uri = shard.uri
            if uri.startswith("file://"):
                uri = uri[7:]
            elif uri.startswith("local://"):
                settings = get_settings()
                uri = str(settings.workspace_root / uri[8:])
            uris.append(uri)
        elif shard.key:
            # Resolve key to local path
            settings = get_settings()
            ws, name = source.split("/", 1)
            version = ds.manifest.version_hash
            local_path = settings.workspace_root / "data" / ws / name / version / shard.key
            if local_path.exists():
                uris.append(str(local_path))

    if not uris:
        raise ValueError(f"No accessible shards for {source}")

    # Create relation from parquet files
    if len(uris) == 1:
        return conn.read_parquet(uris[0])
    else:
        return conn.read_parquet(uris)


def schema(source: str) -> dict[str, str]:
    """Get column names and types.

    Args:
        source: Dataset ID

    Returns:
        Dict mapping column names to DuckDB type strings
    """
    ds = dataset(source)
    tbl = ds.table("main")
    return tbl.schema()


def head(source: str, n: int = 5) -> "duckdb.DuckDBPyRelation":
    """Preview first n rows.

    Args:
        source: Dataset ID
        n: Number of rows

    Returns:
        DuckDB relation with first n rows
    """
    rel = load(source)
    return rel.limit(n)


def dataset_info(source: str) -> dict[str, Any]:
    """Get dataset metadata.

    Args:
        source: Dataset ID

    Returns:
        Dict with workspace, name, version, manifest info, etc.
    """
    ds = dataset(source)
    manifest = ds.manifest

    workspace, name = source.split("/", 1)

    # Build schema
    tbl = ds.table("main")
    schema_dict = tbl.schema()

    # Build resources list
    resources = []
    for shard in tbl.descriptor.shards:
        resources.append({
            "uri": shard.uri or f"key:{shard.key}",
            "size": shard.byte_size,
            "checksum": None,
            "type": "file",
        })

    return {
        "workspace": workspace,
        "name": name,
        "version_hash": manifest.version_hash,
        "manifest": {
            "schema": schema_dict,
            "resources": resources,
            "format": "parquet",
            "row_count": tbl.row_count,
            "metadata": {},
        },
    }


def is_image_dataset(source: str) -> bool:
    """Check if dataset has image columns.

    Args:
        source: Dataset ID

    Returns:
        True if dataset has bound image artifacts
    """
    ds = dataset(source)
    manifest = ds.manifest

    # Check bindings for image media type
    for binding in manifest.bindings:
        if binding.media_type == "image":
            return True

    return False


def load_images(source: str) -> "pd.DataFrame":
    """Load image dataset with PIL decoding.

    Args:
        source: Dataset ID

    Returns:
        DataFrame with image columns decoded as PIL Images
    """
    import pandas as pd
    from PIL import Image
    import io

    ds = dataset(source)
    tbl = ds.table("main")

    # Find image columns
    image_cols = []
    for binding in ds.manifest.bindings:
        if binding.media_type == "image":
            image_cols.append(binding.column)

    # Load data with refs wrapped
    rows = []
    for batch in tbl.batches(batch_size=100, as_format="dict", wrap_refs=True):
        n_rows = len(next(iter(batch.values())))
        for i in range(n_rows):
            row = {}
            for col, values in batch.items():
                val = values[i]
                # Decode image refs
                if col in image_cols and hasattr(val, "read_bytes"):
                    try:
                        data = val.read_bytes()
                        row[col] = Image.open(io.BytesIO(data))
                    except Exception:
                        row[col] = None
                else:
                    row[col] = val
            rows.append(row)

    return pd.DataFrame(rows)


def register_dataset(path: str | Path, name: str | None = None) -> str:
    """Register a local dataset.

    Args:
        path: Path to parquet file or directory
        name: Dataset name (inferred from path if not provided)

    Returns:
        Dataset ID
    """
    import subprocess

    path = Path(path).expanduser().resolve()

    if name is None:
        # Infer name from path
        name = f"local/{path.stem}"

    # Use CLI to register
    cmd = ["warpdata", "register", name, "--table", f"main={path}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Registration failed: {result.stderr}")

    return name


# Module-level aliases for `from warpdatasets.compat import wd` usage
class _CompatModule:
    """Wrapper to make compat usable as `wd.function()`."""
    list_datasets = staticmethod(list_datasets)
    load = staticmethod(load)
    schema = staticmethod(schema)
    head = staticmethod(head)
    dataset_info = staticmethod(dataset_info)
    is_image_dataset = staticmethod(is_image_dataset)
    load_images = staticmethod(load_images)
    register_dataset = staticmethod(register_dataset)


wd = _CompatModule()
