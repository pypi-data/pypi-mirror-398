"""warpdata inspect command - show artifacts and bindings."""

from __future__ import annotations

import sys
from argparse import Namespace

import warpdatasets as wd
from warpdatasets.util.errors import WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the inspect command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        ds = wd.dataset(args.dataset, version=args.ds_version)
    except WarpDatasetsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    manifest = ds.manifest

    # Print tables
    print("Tables:")
    for name, table in manifest.tables.items():
        row_info = f", {table.row_count:,} rows" if table.row_count else ""
        print(f"  {name}: {len(table.shards)} shard(s){row_info}")

    # Print artifacts
    if manifest.artifacts:
        print("\nArtifacts:")
        for name, artifact in manifest.artifacts.items():
            compression = f", {artifact.compression}" if artifact.compression else ""
            print(f"  {name}: {artifact.kind}, {len(artifact.shards)} shard(s){compression}")
    else:
        print("\nArtifacts: (none)")

    # Print bindings
    if manifest.bindings:
        print("\nBindings:")
        for binding in manifest.bindings:
            print(f"  {binding.table}.{binding.column} -> {binding.artifact}")
            print(f"    ref_type: {binding.ref_type}, media_type: {binding.media_type}")
    else:
        print("\nBindings: (none)")

    return 0
