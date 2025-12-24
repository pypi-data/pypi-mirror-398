"""warpdata ingest command - convert raw data to datasets.

Subcommands:
- imagefolder: Ingest ImageNet-style directory structures
- paired: Ingest paired data (image+mask, audio+transcript)
- csv: Ingest CSV with file path columns
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path


def run(args: Namespace) -> int:
    """Run the ingest command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    subcommand = getattr(args, "ingest_command", None)

    if subcommand is None:
        print("usage: warpdata ingest {imagefolder,paired,csv}", file=sys.stderr)
        return 1

    if subcommand == "imagefolder":
        return _run_imagefolder(args)
    elif subcommand == "paired":
        return _run_paired(args)
    elif subcommand == "csv":
        return _run_csv(args)
    else:
        print(f"Unknown subcommand: {subcommand}", file=sys.stderr)
        return 1


def _parse_pairs(pair_args: list[str] | None) -> dict[str, tuple[str, str]]:
    """Parse --pair arguments into dict.

    Format: name=dir:pattern
    Example: masks=/data/masks:{id}.npy
    """
    if not pair_args:
        return {}

    pairs = {}
    for arg in pair_args:
        if "=" not in arg:
            raise ValueError(f"Invalid pair format: {arg}. Expected name=dir:pattern")

        name, rest = arg.split("=", 1)

        if ":" not in rest:
            raise ValueError(f"Invalid pair format: {arg}. Expected name=dir:pattern")

        # Handle paths with colons (Windows) by splitting from the right
        # Pattern should be simple like {id}.npy
        parts = rest.rsplit(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid pair format: {arg}. Expected name=dir:pattern")

        dir_path, pattern = parts
        pairs[name.strip()] = (dir_path.strip(), pattern.strip())

    return pairs


def _run_imagefolder(args: Namespace) -> int:
    """Ingest an ImageNet-style directory."""
    from warpdatasets.ingest import imagefolder, PairSpec

    images_dir = Path(args.images).expanduser().resolve()

    if not images_dir.is_dir():
        print(f"Error: Images directory not found: {images_dir}", file=sys.stderr)
        return 1

    # Parse pairs
    try:
        pairs = _parse_pairs(getattr(args, "pair", None))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Validate pair directories
    for name, (dir_path, pattern) in pairs.items():
        pair_dir = Path(dir_path).expanduser().resolve()
        if not pair_dir.is_dir():
            print(f"Error: Pair directory not found: {pair_dir} (for {name})", file=sys.stderr)
            return 1

    # Determine workspace root
    workspace_root = None
    if args.workspace_root:
        workspace_root = Path(args.workspace_root).expanduser()

    try:
        result = imagefolder(
            dataset_id=args.dataset,
            images_dir=images_dir,
            labels=args.labels,
            id_strategy=args.id,
            pairs=pairs,
            workspace_root=workspace_root,
            progress=True,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print("Dry run - no changes made")
            print()
            print(result.summary())
            print()
            print("Sample rows:")
            for row in result.table_data[:3]:
                print(f"  {row}")
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _run_paired(args: Namespace) -> int:
    """Ingest paired data from multiple directories."""
    from warpdatasets.ingest import paired

    # Parse primary source
    if not args.primary:
        print("Error: --primary is required", file=sys.stderr)
        return 1

    try:
        primary = _parse_source(args.primary)
    except ValueError as e:
        print(f"Error parsing --primary: {e}", file=sys.stderr)
        return 1

    # Parse secondary sources
    secondaries = []
    if args.secondary:
        for sec_arg in args.secondary:
            try:
                secondaries.append(_parse_source(sec_arg))
            except ValueError as e:
                print(f"Error parsing --secondary: {e}", file=sys.stderr)
                return 1

    workspace_root = None
    if args.workspace_root:
        workspace_root = Path(args.workspace_root).expanduser()

    try:
        result = paired(
            dataset_id=args.dataset,
            primary=primary,
            secondaries=secondaries if secondaries else None,
            id_strategy=args.id,
            workspace_root=workspace_root,
            progress=True,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print("Dry run - no changes made")
            print()
            print(result.summary())
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _parse_source(arg: str) -> tuple[str, str, str | None, str]:
    """Parse a source argument: name=dir[:pattern]:media_type

    Returns (name, dir, pattern, media_type)
    """
    if "=" not in arg:
        raise ValueError(f"Expected name=dir[:pattern]:media_type, got: {arg}")

    name, rest = arg.split("=", 1)

    # Split by : from the right to handle paths with colons
    parts = rest.split(":")

    if len(parts) < 2:
        raise ValueError(f"Expected at least dir:media_type, got: {rest}")

    # Last part is media_type
    media_type = parts[-1].strip()
    if media_type not in ("image", "audio", "video", "file"):
        raise ValueError(f"Invalid media_type: {media_type}. Expected image/audio/video/file")

    # Second to last might be pattern or dir
    if len(parts) == 2:
        # name=dir:media_type
        dir_path = parts[0].strip()
        pattern = None
    elif len(parts) == 3:
        # name=dir:pattern:media_type
        dir_path = parts[0].strip()
        pattern = parts[1].strip()
    else:
        # Handle paths with colons (join all but last two)
        dir_path = ":".join(parts[:-2]).strip()
        pattern = parts[-2].strip() if parts[-2].strip() else None

    return (name.strip(), dir_path, pattern, media_type)


def _run_csv(args: Namespace) -> int:
    """Ingest CSV with file path columns."""
    from warpdatasets.ingest import csv_files

    csv_path = Path(args.csv).expanduser().resolve()

    if not csv_path.is_file():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        return 1

    # Parse file columns: column=artifact:dir:media_type
    file_columns = {}
    if args.file_column:
        for fc_arg in args.file_column:
            try:
                col, artifact, dir_path, media_type = _parse_file_column(fc_arg)
                file_columns[col] = (artifact, dir_path, media_type)
            except ValueError as e:
                print(f"Error parsing --file-column: {e}", file=sys.stderr)
                return 1

    if not file_columns:
        print("Error: At least one --file-column is required", file=sys.stderr)
        return 1

    workspace_root = None
    if args.workspace_root:
        workspace_root = Path(args.workspace_root).expanduser()

    try:
        result = csv_files(
            dataset_id=args.dataset,
            csv_path=csv_path,
            file_columns=file_columns,
            id_column=args.id_column,
            workspace_root=workspace_root,
            progress=True,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print("Dry run - no changes made")
            print()
            print(result.summary())
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _parse_file_column(arg: str) -> tuple[str, str, str, str]:
    """Parse a file column argument: csv_column=artifact:dir:media_type

    Returns (csv_column, artifact_name, dir, media_type)
    """
    if "=" not in arg:
        raise ValueError(f"Expected csv_column=artifact:dir:media_type, got: {arg}")

    col, rest = arg.split("=", 1)
    parts = rest.split(":")

    if len(parts) < 3:
        raise ValueError(f"Expected artifact:dir:media_type, got: {rest}")

    artifact = parts[0].strip()
    media_type = parts[-1].strip()

    if media_type not in ("image", "audio", "video", "file"):
        raise ValueError(f"Invalid media_type: {media_type}")

    # Dir is everything in between
    dir_path = ":".join(parts[1:-1]).strip()

    return (col.strip(), artifact, dir_path, media_type)
