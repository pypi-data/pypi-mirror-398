"""warpdata embeddings command - manage dataset embeddings.

Subcommands:
- list: List embeddings for a dataset
- add: Build embeddings locally
- info: Show embedding details
- publish: Publish embeddings to remote storage
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import warpdatasets as wd
from warpdatasets.addons import (
    build_embeddings,
    publish_addon,
    update_manifest_with_addon,
    save_manifest,
)


def run(args: Namespace) -> int:
    """Run the embeddings command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    subcommand = getattr(args, "embeddings_command", None)

    if subcommand is None:
        print("usage: warpdata embeddings {list,add,info,publish}", file=sys.stderr)
        return 1

    if subcommand == "list":
        return _run_list(args)
    elif subcommand == "add":
        return _run_add(args)
    elif subcommand == "info":
        return _run_info(args)
    elif subcommand == "publish":
        return _run_publish(args)
    else:
        print(f"Unknown subcommand: {subcommand}", file=sys.stderr)
        return 1


def _run_list(args: Namespace) -> int:
    """List embeddings for a dataset."""
    try:
        ds = wd.dataset(args.dataset, version=getattr(args, "ds_version", None))
    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        return 1

    # Find embedding addons
    embedding_addons = {
        name: addon for name, addon in ds.manifest.addons.items()
        if addon.is_embedding
    }

    if not embedding_addons:
        print(f"No embeddings found for {args.dataset}")
        return 0

    print(f"Embeddings for {args.dataset}:")
    print()

    for name, addon in embedding_addons.items():
        params = addon.params
        row_count = addon.vectors.row_count if addon.vectors else "?"
        has_index = "yes" if addon.index else "no"

        print(f"  {name}")
        print(f"    Provider: {params.provider if params else '?'}")
        print(f"    Model: {params.model if params else '?'}")
        print(f"    Dims: {params.dims if params else '?'}")
        print(f"    Vectors: {row_count}")
        print(f"    Index: {has_index}")
        print()

    return 0


def _run_add(args: Namespace) -> int:
    """Build embeddings for a dataset."""
    try:
        ds = wd.dataset(args.dataset, version=getattr(args, "ds_version", None))
    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        return 1

    # Parse source columns
    source_columns = None
    if args.columns:
        source_columns = [c.strip() for c in args.columns.split(",")]

    # Determine key column
    key_column = args.key or "id"

    # Build embeddings
    print(f"Building embeddings: {args.name}")
    print(f"  Provider: {args.provider}")
    print(f"  Model: {args.model}")
    print(f"  Dims: {args.dims}")
    print(f"  Table: {args.table}")
    print(f"  Key column: {key_column}")
    if source_columns:
        print(f"  Source columns: {', '.join(source_columns)}")
    print()

    try:
        addon = build_embeddings(
            dataset=ds,
            name=args.name,
            provider=args.provider,
            model=args.model,
            dims=args.dims,
            source_columns=source_columns,
            table=args.table,
            key_column=key_column,
            metric=args.metric,
            normalized=not args.no_normalize,
            batch_size=args.batch_size,
            build_index=args.index,
            index_type=args.index_type,
            output_dir=args.output if args.output else None,
            progress=True,
        )
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error building embeddings: {e}", file=sys.stderr)
        return 1

    print()
    print(f"Embeddings built successfully!")
    print(f"  Vectors: {addon.vectors.row_count if addon.vectors else 0}")
    print(f"  Index: {'yes' if addon.index else 'no'}")

    if addon.vectors and addon.vectors.shards:
        print(f"  Location: {addon.vectors.shards[0].uri}")

    return 0


def _run_info(args: Namespace) -> int:
    """Show embedding details."""
    try:
        ds = wd.dataset(args.dataset, version=getattr(args, "ds_version", None))
    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        return 1

    # Get embedding space
    try:
        space = ds.embeddings(args.name)
    except KeyError as e:
        print(f"Embedding not found: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    info = space.info()

    print(f"Embedding: {info['name']}")
    print()
    print(f"Base table: {info['base_table']}")
    print(f"Key: {info['key']['column']} ({info['key']['type']})")
    print()

    if "params" in info:
        params = info["params"]
        print("Parameters:")
        print(f"  Provider: {params['provider']}")
        print(f"  Model: {params['model']}")
        print(f"  Dims: {params['dims']}")
        print(f"  Metric: {params['metric']}")
        print(f"  Normalized: {params['normalized']}")
        if params["source_columns"]:
            print(f"  Source columns: {', '.join(params['source_columns'])}")
        print()

    if "vectors" in info:
        print("Vectors:")
        print(f"  Shards: {info['vectors']['shards']}")
        print(f"  Row count: {info['vectors']['row_count']}")
        print()

    if "index" in info:
        print("Index:")
        print(f"  Kind: {info['index']['kind']}")
        if info["index"]["byte_size"]:
            size_mb = info["index"]["byte_size"] / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
        print()

    return 0


def _run_publish(args: Namespace) -> int:
    """Publish embeddings to remote storage."""
    try:
        ds = wd.dataset(args.dataset, version=getattr(args, "ds_version", None))
    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        return 1

    # Get the addon
    if args.name not in ds.manifest.addons:
        print(f"Addon not found: {args.name}", file=sys.stderr)
        print(f"Available addons: {', '.join(ds.manifest.addons.keys()) or '(none)'}")
        return 1

    addon = ds.manifest.addons[args.name]

    # Get base URI
    base_uri = args.base_uri
    if not base_uri:
        from warpdatasets.config import get_settings
        settings = get_settings()
        if not settings.manifest_base:
            print("No base URI provided and WARPDATASETS_MANIFEST_BASE not set", file=sys.stderr)
            return 1
        base_uri = settings.manifest_base

    print(f"Publishing embedding: {args.name}")
    print(f"  Destination: {base_uri}")
    print()

    try:
        published_addon = publish_addon(
            addon=addon,
            addon_name=args.name,
            dataset_id=ds.id,
            dataset_version=ds.version_hash,
            base_uri=base_uri,
            force=args.force,
            dry_run=args.dry_run,
            progress=True,
        )
    except Exception as e:
        print(f"Error publishing: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print()
        print("Dry run complete. No files were uploaded.")
        return 0

    print()
    print("Published successfully!")

    if published_addon.vectors and published_addon.vectors.shards:
        print(f"  Vectors: {published_addon.vectors.shards[0].uri}")
    if published_addon.index:
        print(f"  Index: {published_addon.index.uri}")

    return 0
