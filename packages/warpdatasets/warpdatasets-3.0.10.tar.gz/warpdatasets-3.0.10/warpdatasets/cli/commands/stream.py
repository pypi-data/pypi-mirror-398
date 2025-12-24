"""warpdata stream command - stream batches from a table."""

from __future__ import annotations

import sys
from argparse import Namespace

import warpdatasets as wd
from warpdatasets.util.errors import WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the stream command.

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

    # Parse shard
    shard = None
    if args.shard:
        if args.shard == "auto":
            shard = "auto"
        else:
            try:
                rank, world = args.shard.split(",")
                shard = (int(rank), int(world))
            except ValueError:
                print(f"Error: Invalid shard format '{args.shard}'. Use 'auto' or 'rank,world'",
                      file=sys.stderr)
                return 1

    # Parse columns
    columns = None
    if args.columns:
        columns = [c.strip() for c in args.columns.split(",")]

    # Stream batches
    total_rows = 0
    total_batches = 0

    try:
        for batch in table.batches(
            batch_size=args.batch_size,
            columns=columns,
            shard=shard,
            limit=args.limit,
        ):
            total_batches += 1
            total_rows += batch.num_rows

            if args.verbose and total_batches % 10 == 0:
                print(f"Streamed {total_batches} batches, {total_rows:,} rows...",
                      file=sys.stderr)

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)

    # Print summary
    print(f"Streamed {total_batches} batches, {total_rows:,} rows total")

    if args.show_schema:
        print("\nSchema:")
        schema = table.schema()
        for name, dtype in schema.items():
            print(f"  {name}: {dtype}")

    return 0
