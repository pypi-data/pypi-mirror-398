"""Cache management CLI commands."""

from __future__ import annotations

import argparse
import sys


def run_status(args: argparse.Namespace) -> int:
    """Run cache status command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from warpdatasets.config.settings import get_settings
    from warpdatasets.cache.blob_cache import BlobCache

    settings = get_settings()
    cache = BlobCache(cache_dir=settings.cache_dir / "blobs")

    stats = cache.stats()

    # Format size
    def format_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    print("Cache Status")
    print("=" * 40)
    print(f"Directory:    {settings.cache_dir}")
    print(f"Total size:   {format_size(stats.total_bytes)}")
    print(f"Entries:      {stats.entry_count}")
    print(f"Hits:         {stats.hits}")
    print(f"Misses:       {stats.misses}")

    if stats.hits + stats.misses > 0:
        hit_rate = stats.hits / (stats.hits + stats.misses) * 100
        print(f"Hit rate:     {hit_rate:.1f}%")

    return 0


def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes.

    Args:
        size_str: Size string like "1GB", "500MB", "1024"

    Returns:
        Size in bytes

    Raises:
        ValueError: If format is invalid
    """
    size_str = size_str.strip().upper()

    multipliers = {
        "B": 1,
        "KB": 1024,
        "K": 1024,
        "MB": 1024 * 1024,
        "M": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "G": 1024 * 1024 * 1024,
        "TB": 1024 * 1024 * 1024 * 1024,
        "T": 1024 * 1024 * 1024 * 1024,
    }

    for suffix, mult in multipliers.items():
        if size_str.endswith(suffix):
            num_str = size_str[: -len(suffix)].strip()
            return int(float(num_str) * mult)

    # No suffix, assume bytes
    return int(size_str)


def run_gc(args: argparse.Namespace) -> int:
    """Run cache garbage collection command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from warpdatasets.config.settings import get_settings
    from warpdatasets.cache.blob_cache import BlobCache

    settings = get_settings()
    cache = BlobCache(cache_dir=settings.cache_dir / "blobs")

    # Get current size
    stats = cache.stats()
    print(f"Current cache size: {stats.total_bytes:,} bytes ({stats.entry_count} entries)")

    # Parse target size
    target_bytes = parse_size(args.target)

    if stats.total_bytes <= target_bytes:
        print(f"Already at or below target ({target_bytes:,} bytes). Nothing to do.")
        return 0

    # Run GC
    print(f"Reducing to target: {target_bytes:,} bytes")
    freed = cache.gc(target_bytes)

    print(f"Freed: {freed:,} bytes")

    # Show new stats
    stats = cache.stats()
    print(f"New cache size: {stats.total_bytes:,} bytes ({stats.entry_count} entries)")

    return 0


def run_clear(args: argparse.Namespace) -> int:
    """Run cache clear command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from warpdatasets.config.settings import get_settings
    from warpdatasets.cache.blob_cache import BlobCache

    settings = get_settings()
    cache = BlobCache(cache_dir=settings.cache_dir / "blobs")

    # Get current size
    stats = cache.stats()
    print(f"Current cache: {stats.total_bytes:,} bytes ({stats.entry_count} entries)")

    if stats.entry_count == 0:
        print("Cache is already empty.")
        return 0

    if not args.yes:
        response = input("Clear entire cache? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            return 0

    # Clear by GCing to 0
    freed = cache.gc(0)
    print(f"Cleared {freed:,} bytes")

    return 0


def run(args: argparse.Namespace) -> int:
    """Run cache command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.cache_command == "status":
        return run_status(args)
    elif args.cache_command == "gc":
        return run_gc(args)
    elif args.cache_command == "clear":
        return run_clear(args)
    else:
        print(f"Unknown cache command: {args.cache_command}", file=sys.stderr)
        return 1
