"""warpdata schema command - show table schema."""

from __future__ import annotations

import sys
from argparse import Namespace

import warpdatasets as wd
from warpdatasets.util.errors import WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the schema command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        ds = wd.dataset(args.dataset, version=args.ds_version)
        table = ds.table(args.table)
    except WarpDatasetsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    schema = table.schema()

    # Find max column name length for alignment
    max_name_len = max(len(name) for name in schema.keys()) if schema else 0

    print(f"Schema for {args.dataset}/{args.table}:")
    print()

    for name, dtype in schema.items():
        print(f"  {name:<{max_name_len}}  {dtype}")

    print()
    print(f"Total columns: {len(schema)}")

    return 0
