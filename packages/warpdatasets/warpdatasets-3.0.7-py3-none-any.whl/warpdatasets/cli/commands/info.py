"""warpdata info command - show dataset information."""

from __future__ import annotations

import json
import sys
from argparse import Namespace

import warpdatasets as wd
from warpdatasets.util.errors import WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the info command.

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

    info = ds.info()

    # Print formatted info
    print(f"Dataset: {info['id']}")
    print(f"Version: {info['version']}")
    print()

    print("Tables:")
    for name, table_info in info["tables"].items():
        print(f"  {name}:")
        print(f"    Format: {table_info['format']}")
        print(f"    Shards: {table_info['shards']}")
        if table_info["row_count"]:
            print(f"    Rows: {table_info['row_count']:,}")
        if table_info["schema"]:
            print(f"    Columns: {len(table_info['schema'])}")

    if info["artifacts"]:
        print()
        print("Artifacts:")
        for name in info["artifacts"]:
            print(f"  - {name}")

    if info["bindings"]:
        print()
        print(f"Bindings: {info['bindings']}")

    return 0
