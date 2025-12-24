"""Warm cache CLI command."""

from __future__ import annotations

import argparse
import sys


def run(args: argparse.Namespace) -> int:
    """Run warm command.

    Downloads shards for a dataset to warm the cache.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from warpdatasets.api.dataset import dataset as get_dataset
    from warpdatasets.cache.context import CacheContext
    from warpdatasets.config.settings import get_settings

    settings = get_settings()

    # Load dataset
    print(f"Loading dataset: {args.dataset}")
    ds = get_dataset(
        args.dataset,
        version=args.ds_version,
        settings=settings,
    )

    # Get table
    table = ds.table(args.table)
    print(f"Table: {args.table}")
    print(f"Shards: {table.shard_count}")

    # Get URIs to warm
    uris = table.descriptor.uris

    # If --artifacts specified, add artifact shards
    artifact_uris = []
    if args.artifacts:
        artifact_names = args.artifacts.split(",")
        for name in artifact_names:
            name = name.strip()
            if name in ds.manifest.artifacts:
                artifact = ds.manifest.artifacts[name]
                artifact_uris.extend(artifact.uris)
                print(f"Artifact '{name}': {len(artifact.uris)} shards")
            else:
                print(f"Warning: Artifact '{name}' not found", file=sys.stderr)

    all_uris = list(uris) + artifact_uris
    print(f"Total URIs to warm: {len(all_uris)}")

    # Create cache context for warming
    cache_context = CacheContext(
        cache_dir=settings.cache_dir,
        prefetch_mode="off",  # We'll use warm() directly
    )

    # Count already cached
    cached = sum(1 for uri in all_uris if cache_context.is_cached(uri))
    to_download = len(all_uris) - cached

    print(f"Already cached: {cached}")
    print(f"To download: {to_download}")

    if to_download == 0:
        print("All shards already cached!")
        return 0

    if not args.yes:
        response = input(f"Download {to_download} shards? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            return 0

    # Warm cache
    print("Warming cache...")
    downloaded = cache_context.warm(all_uris)
    print(f"Downloaded: {downloaded} shards")

    # Show stats
    stats = cache_context.stats()
    print(f"Cache size: {stats['cache']['total_bytes']:,} bytes")
    print(f"Cache entries: {stats['cache']['entry_count']}")

    return 0
