"""warpdata head command - preview first rows."""

from __future__ import annotations

import json
import sys
from argparse import Namespace

import warpdatasets as wd
from warpdatasets.util.errors import WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the head command.

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

    # Get first n rows
    relation = table.head(args.rows)

    if args.format == "json":
        # Convert to list of dicts
        df = relation.df()
        records = df.to_dict(orient="records")
        print(json.dumps(records, indent=2, default=str))

    elif args.format == "csv":
        df = relation.df()
        print(df.to_csv(index=False))

    else:  # table format
        # Use DuckDB's built-in display
        print(relation)

    return 0
