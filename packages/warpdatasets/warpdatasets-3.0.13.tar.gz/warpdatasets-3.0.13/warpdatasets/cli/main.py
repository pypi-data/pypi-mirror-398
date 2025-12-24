"""CLI entrypoint for warpdata command."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from warpdatasets.cli.commands import info, schema, head, stream, inspect, cat, cache, warm, publish, ls, register, init, doctor, embeddings, ingest, sync


MAIN_HELP = """\
WarpDatasets - Fast, remote-first dataset library for ML

Load any dataset with a single line of Python:

  import warpdatasets as wd
  ds = wd.dataset("vision/cifar10")

Iterate over rows:

  for row in ds.rows():
      image = row["image"]
      label = row["label"]

Stream batches for training:

  for batch in ds.table("main").batches(batch_size=64):
      images = batch["image"]  # numpy array

SQL queries via DuckDB:

  df = ds.table("main").query("SELECT * WHERE label = 'cat' LIMIT 100")

Add embeddings:

  ds.build_embeddings(model="clip", column="image")
  similar = ds.embeddings("clip").search(query_vector, k=10)

Environment variables:
  WARPDATASETS_ROOT     Workspace root (default: ~/.warpdatasets)
  WARPDATASETS_SCOPE    'local' or 'remote' (default: local)
  AWS_PROFILE           AWS profile for S3 access
"""

EXAMPLES = """\
Examples:

  # List all datasets
  warpdata ls

  # Preview first 10 rows
  warpdata head vision/mnist -n 10

  # Show schema
  warpdata schema nlp/imdb

  # Sync with S3 (pull on new machine, push to share)
  warpdata sync pull                    # download all manifests from S3
  warpdata sync push                    # upload local manifests to S3
  warpdata sync status                  # compare local vs S3

  # Register local parquet as dataset
  warpdata register mywork/mydata --table main=./data/*.parquet

  # Ingest image folder (ImageNet style)
  warpdata ingest imagefolder vision/cats_dogs --images ./train --labels from-parent

  # Build embeddings (OpenAI)
  warpdata embeddings add nlp/imdb --name openai-3-small \\
    --provider openai --model text-embedding-3-small --dims 1536 \\
    --columns text --index

  # Build embeddings (local sentence-transformers)
  warpdata embeddings add nlp/imdb --name mpnet \\
    --provider sentence-transformers --model all-mpnet-base-v2 --dims 768 \\
    --columns text

  # List/inspect embeddings
  warpdata embeddings list nlp/imdb
  warpdata embeddings info nlp/imdb --name openai-3-small

Python quick start:

  import warpdatasets as wd

  # Load dataset
  ds = wd.dataset("vision/mnist")

  # Iterate rows
  for row in ds.rows():
      print(row["label"], row["image"].shape)

  # Batch streaming
  for batch in ds.table("main").batches(batch_size=32):
      X = batch["image"]  # (32, 28, 28) numpy array
      y = batch["label"]  # (32,) numpy array

  # SQL query
  df = ds.table("main").query("SELECT label, COUNT(*) as n GROUP BY label")

  # Build embeddings
  from warpdatasets.addons import build_embeddings
  build_embeddings(ds, name="openai", provider="openai",
                   model="text-embedding-3-small", dims=1536,
                   source_columns=["text"], build_index=True)

  # Search embeddings
  space = ds.embeddings("openai")
  results = space.search(query_vec, k=10)

Docs: https://github.com/anthropics/warpdatasets
"""


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="warpdata",
        description=MAIN_HELP,
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
    )

    # ls command (list local datasets)
    ls_parser = subparsers.add_parser(
        "ls",
        help="List local datasets",
        description="List datasets registered in the local workspace",
    )
    ls_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory (default: from settings)",
    )
    ls_parser.add_argument(
        "--all",
        "-a",
        dest="all_versions",
        action="store_true",
        help="Show all versions, not just latest",
    )
    ls_parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    # register command (register local dataset)
    register_parser = subparsers.add_parser(
        "register",
        help="Register a local dataset",
        description="Create a local manifest from parquet files and optional artifact directories",
    )
    register_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    register_parser.add_argument(
        "--table",
        "-t",
        action="append",
        help="Table: name=path/to/shards/*.parquet (can repeat, 'main' required)",
    )
    register_parser.add_argument(
        "--artifact",
        "-a",
        action="append",
        help="Artifact: name=path/to/directory[:media_type] (can repeat)",
    )
    register_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory (default: from settings)",
    )
    register_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing manifest",
    )

    # init command (generate loader)
    init_parser = subparsers.add_parser(
        "init",
        help="Generate a dataset loader",
        description="Generate a runnable Python file tailored to a dataset",
    )
    init_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    init_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: derived from dataset ID)",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file",
    )
    init_parser.add_argument(
        "--print",
        action="store_true",
        help="Print generated code to stdout",
    )
    init_parser.add_argument(
        "--table",
        "-t",
        default="main",
        help="Table to scaffold against (default: main)",
    )
    init_parser.add_argument(
        "--mode",
        choices=["auto", "remote", "hybrid", "local"],
        default="auto",
        help="Default access mode (default: auto)",
    )
    init_parser.add_argument(
        "--prefetch",
        choices=["off", "auto", "aggressive"],
        default="auto",
        help="Default prefetch mode (default: auto)",
    )
    init_parser.add_argument(
        "--include-refs",
        dest="include_refs",
        action="store_true",
        default=None,
        help="Generate ref decode helpers (default: auto based on bindings)",
    )
    init_parser.add_argument(
        "--no-refs",
        dest="include_refs",
        action="store_false",
        help="Skip ref decode helpers",
    )
    init_parser.add_argument(
        "--columns",
        "-c",
        help="Comma-separated column names to include",
    )
    init_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show dataset information",
        description="Display manifest and metadata for a dataset",
    )
    info_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    info_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # schema command
    schema_parser = subparsers.add_parser(
        "schema",
        help="Show table schema",
        description="Display column names and types for a table",
    )
    schema_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    schema_parser.add_argument(
        "--table",
        "-t",
        default="main",
        help="Table name (default: main)",
    )
    schema_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # head command
    head_parser = subparsers.add_parser(
        "head",
        help="Preview first rows",
        description="Display first N rows of a table",
    )
    head_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    head_parser.add_argument(
        "-n",
        "--rows",
        type=int,
        default=5,
        help="Number of rows (default: 5)",
    )
    head_parser.add_argument(
        "--table",
        "-t",
        default="main",
        help="Table name (default: main)",
    )
    head_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )
    head_parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )

    # stream command
    stream_parser = subparsers.add_parser(
        "stream",
        help="Stream batches from a table",
        description="Stream Arrow batches for training",
    )
    stream_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    stream_parser.add_argument(
        "--table",
        "-t",
        default="main",
        help="Table name (default: main)",
    )
    stream_parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=50000,
        help="Rows per batch (default: 50000)",
    )
    stream_parser.add_argument(
        "--columns",
        "-c",
        help="Comma-separated column names to select",
    )
    stream_parser.add_argument(
        "--shard",
        "-s",
        help="Shard config: 'auto' or 'rank,world' (e.g., '0,4')",
    )
    stream_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        help="Maximum rows to stream",
    )
    stream_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )
    stream_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress during streaming",
    )
    stream_parser.add_argument(
        "--show-schema",
        action="store_true",
        help="Print schema after streaming",
    )

    # inspect command
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Show artifacts and bindings",
        description="Display artifacts, bindings, and table info for a dataset",
    )
    inspect_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    inspect_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # cat command
    cat_parser = subparsers.add_parser(
        "cat",
        help="Output artifact member bytes",
        description="Fetch and output bytes from an artifact member",
    )
    cat_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    cat_parser.add_argument(
        "--artifact",
        "-a",
        required=True,
        help="Artifact name",
    )
    cat_parser.add_argument(
        "--ref",
        "-r",
        required=True,
        help="Reference value (e.g., member path)",
    )
    cat_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )
    cat_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    )
    cat_parser.add_argument(
        "--info",
        action="store_true",
        help="Print metadata instead of bytes",
    )
    cat_parser.add_argument(
        "--show-image",
        action="store_true",
        help="Display image info (requires Pillow)",
    )

    # cache command (with subcommands)
    cache_parser = subparsers.add_parser(
        "cache",
        help="Cache management",
        description="Manage local blob cache",
    )
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_command",
        title="cache commands",
        description="Cache management commands",
    )

    # cache status
    cache_status_parser = cache_subparsers.add_parser(
        "status",
        help="Show cache statistics",
    )

    # cache gc
    cache_gc_parser = cache_subparsers.add_parser(
        "gc",
        help="Run garbage collection",
    )
    cache_gc_parser.add_argument(
        "--target",
        "-t",
        default="0",
        help="Target size (e.g., '1GB', '500MB'). Default: 0 (clear all)",
    )

    # cache clear
    cache_clear_parser = cache_subparsers.add_parser(
        "clear",
        help="Clear entire cache",
    )
    cache_clear_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation",
    )

    # warm command
    warm_parser = subparsers.add_parser(
        "warm",
        help="Pre-download shards to cache",
        description="Download dataset shards to warm the cache",
    )
    warm_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    warm_parser.add_argument(
        "--table",
        "-t",
        default="main",
        help="Table name (default: main)",
    )
    warm_parser.add_argument(
        "--artifacts",
        "-a",
        help="Comma-separated artifact names to warm",
    )
    warm_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )
    warm_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation",
    )

    # publish command
    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish a dataset",
        description="Build and publish a dataset to remote storage",
    )
    publish_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    publish_parser.add_argument(
        "--table",
        "-t",
        action="append",
        help="Table definition: name=path/to/shards/*.parquet (can repeat)",
    )
    publish_parser.add_argument(
        "--artifact",
        "-a",
        action="append",
        help="Artifact definition: name=path/to/directory (can repeat)",
    )
    publish_parser.add_argument(
        "--bind",
        "-b",
        action="append",
        help="Binding: table.column=artifact:media_type[:ref_type] (can repeat)",
    )
    publish_parser.add_argument(
        "--base-uri",
        help="Base storage URI (e.g., s3://bucket/warp)",
    )
    publish_parser.add_argument(
        "--set-latest",
        action="store_true",
        help="Update the latest pointer after publish",
    )
    publish_parser.add_argument(
        "--shard-size",
        default="512MB",
        help="Artifact shard size (default: 512MB)",
    )
    publish_parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Parallel upload threads (default: 4)",
    )
    publish_parser.add_argument(
        "--temp-dir",
        help="Temp directory for packing artifacts",
    )
    publish_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without uploading",
    )
    publish_parser.add_argument(
        "--force",
        action="store_true",
        help="Upload even if shard already exists",
    )
    publish_parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify accessibility after publish",
    )

    # doctor command
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Diagnose environment issues",
        description="Run checks and report on environment configuration",
    )
    doctor_parser.add_argument(
        "dataset",
        nargs="?",
        help="Optional dataset ID to check accessibility",
    )
    doctor_parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    doctor_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information",
    )
    doctor_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    doctor_parser.add_argument(
        "--performance",
        "-p",
        action="store_true",
        help="Run streaming performance check (requires dataset)",
    )

    # embeddings command (with subcommands)
    embeddings_parser = subparsers.add_parser(
        "embeddings",
        help="Manage dataset embeddings",
        description="Build, list, and publish embeddings for datasets",
    )
    embeddings_subparsers = embeddings_parser.add_subparsers(
        dest="embeddings_command",
        title="embeddings commands",
        description="Embedding management commands",
    )

    # embeddings list
    emb_list_parser = embeddings_subparsers.add_parser(
        "list",
        help="List embeddings for a dataset",
    )
    emb_list_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    emb_list_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # embeddings add
    emb_add_parser = embeddings_subparsers.add_parser(
        "add",
        help="Build embeddings for a dataset",
    )
    emb_add_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    emb_add_parser.add_argument(
        "--name",
        required=True,
        help="Name for this embedding (e.g., 'openai:text-embedding-3-small')",
    )
    emb_add_parser.add_argument(
        "--provider",
        required=True,
        help="Embedding provider (openai, sentence-transformers, custom)",
    )
    emb_add_parser.add_argument(
        "--model",
        required=True,
        help="Model name (e.g., 'text-embedding-3-small')",
    )
    emb_add_parser.add_argument(
        "--dims",
        type=int,
        required=True,
        help="Embedding dimensions",
    )
    emb_add_parser.add_argument(
        "--table",
        "-t",
        default="main",
        help="Source table (default: main)",
    )
    emb_add_parser.add_argument(
        "--key",
        "-k",
        help="Key column for joining (default: id)",
    )
    emb_add_parser.add_argument(
        "--columns",
        "-c",
        help="Comma-separated source columns to embed",
    )
    emb_add_parser.add_argument(
        "--metric",
        default="cosine",
        choices=["cosine", "l2", "ip"],
        help="Distance metric (default: cosine)",
    )
    emb_add_parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip vector normalization",
    )
    emb_add_parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding (default: 100)",
    )
    emb_add_parser.add_argument(
        "--index",
        action="store_true",
        help="Build FAISS index",
    )
    emb_add_parser.add_argument(
        "--index-type",
        default="flat",
        help="FAISS index type (default: flat)",
    )
    emb_add_parser.add_argument(
        "--output",
        "-o",
        help="Output directory for embeddings",
    )
    emb_add_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # embeddings info
    emb_info_parser = embeddings_subparsers.add_parser(
        "info",
        help="Show embedding details",
    )
    emb_info_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    emb_info_parser.add_argument(
        "name",
        help="Embedding name",
    )
    emb_info_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # embeddings publish
    emb_publish_parser = embeddings_subparsers.add_parser(
        "publish",
        help="Publish embeddings to remote storage",
    )
    emb_publish_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    emb_publish_parser.add_argument(
        "name",
        help="Embedding name to publish",
    )
    emb_publish_parser.add_argument(
        "--base-uri",
        help="Base storage URI (default: from WARPDATASETS_MANIFEST_BASE)",
    )
    emb_publish_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    emb_publish_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without uploading",
    )
    emb_publish_parser.add_argument(
        "--version",
        "-v",
        dest="ds_version",
        help="Version hash (default: latest)",
    )

    # ingest command (with subcommands)
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Convert raw data to dataset",
        description="Ingest raw data (images, CSVs) into warpdatasets format",
    )
    ingest_subparsers = ingest_parser.add_subparsers(
        dest="ingest_command",
        title="ingest commands",
        description="Data ingestion commands",
    )

    # ingest imagefolder
    ingest_if_parser = ingest_subparsers.add_parser(
        "imagefolder",
        help="Ingest ImageNet-style directory",
    )
    ingest_if_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    ingest_if_parser.add_argument(
        "--images",
        required=True,
        help="Path to images directory",
    )
    ingest_if_parser.add_argument(
        "--labels",
        choices=["from-parent", "none"],
        default="from-parent",
        help="Label strategy (default: from-parent)",
    )
    ingest_if_parser.add_argument(
        "--id",
        choices=["stem", "relative", "hash"],
        default="stem",
        help="ID strategy (default: stem)",
    )
    ingest_if_parser.add_argument(
        "--pair",
        action="append",
        help="Paired artifact: name=dir:{id}.ext (can repeat)",
    )
    ingest_if_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory",
    )
    ingest_if_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without executing",
    )

    # ingest paired
    ingest_paired_parser = ingest_subparsers.add_parser(
        "paired",
        help="Ingest paired data (image+mask, etc.)",
    )
    ingest_paired_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    ingest_paired_parser.add_argument(
        "--primary",
        required=True,
        help="Primary source: name=dir[:pattern]:media_type",
    )
    ingest_paired_parser.add_argument(
        "--secondary",
        action="append",
        help="Secondary source: name=dir[:pattern]:media_type (can repeat)",
    )
    ingest_paired_parser.add_argument(
        "--id",
        choices=["stem", "relative", "hash"],
        default="stem",
        help="ID strategy (default: stem)",
    )
    ingest_paired_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory",
    )
    ingest_paired_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without executing",
    )

    # ingest csv
    ingest_csv_parser = ingest_subparsers.add_parser(
        "csv",
        help="Ingest CSV with file path columns",
    )
    ingest_csv_parser.add_argument(
        "dataset",
        help="Dataset ID (workspace/name)",
    )
    ingest_csv_parser.add_argument(
        "--csv",
        required=True,
        help="Path to CSV file",
    )
    ingest_csv_parser.add_argument(
        "--file-column",
        action="append",
        help="File column: csv_col=artifact:dir:media_type (can repeat)",
    )
    ingest_csv_parser.add_argument(
        "--id-column",
        help="Column to use as ID",
    )
    ingest_csv_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory",
    )
    ingest_csv_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without executing",
    )

    # sync command (push/pull manifests to/from S3)
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync manifests with S3",
        description="Push/pull manifests to/from S3 for sharing datasets across machines",
    )
    sync_subparsers = sync_parser.add_subparsers(
        dest="sync_command",
        title="sync commands",
        description="Sync operations",
    )

    # sync status
    sync_status_parser = sync_subparsers.add_parser(
        "status",
        help="Show sync status between local and S3",
    )
    sync_status_parser.add_argument(
        "--bucket",
        "-b",
        default=None,
        help="S3 bucket name (default: from settings)",
    )
    sync_status_parser.add_argument(
        "--prefix",
        "-p",
        default=None,
        help="S3 key prefix (default: from settings)",
    )
    sync_status_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory",
    )

    # sync push
    sync_push_parser = sync_subparsers.add_parser(
        "push",
        help="Upload local manifests to S3",
    )
    sync_push_parser.add_argument(
        "dataset",
        nargs="?",
        help="Dataset ID to push (default: all)",
    )
    sync_push_parser.add_argument(
        "--bucket",
        "-b",
        default=None,
        help="S3 bucket name (default: from settings)",
    )
    sync_push_parser.add_argument(
        "--prefix",
        "-p",
        default=None,
        help="S3 key prefix (default: from settings)",
    )
    sync_push_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory",
    )

    # sync pull
    sync_pull_parser = sync_subparsers.add_parser(
        "pull",
        help="Download manifests from S3",
    )
    sync_pull_parser.add_argument(
        "dataset",
        nargs="?",
        help="Dataset ID to pull (default: all)",
    )
    sync_pull_parser.add_argument(
        "--bucket",
        "-b",
        default=None,
        help="S3 bucket name (default: from settings)",
    )
    sync_pull_parser.add_argument(
        "--prefix",
        "-p",
        default=None,
        help="S3 key prefix (default: from settings)",
    )
    sync_pull_parser.add_argument(
        "--workspace-root",
        "-w",
        help="Workspace root directory",
    )
    sync_pull_parser.add_argument(
        "--data",
        "-d",
        action="store_true",
        help="Also download data shards into local mirror",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Hidden alias: "list" -> "ls"
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "list":
        argv = ["ls"] + argv[1:]

    parser = create_parser()
    args = parser.parse_args(argv)

    if args.version:
        from warpdatasets import __version__

        print(f"warpdata {__version__}")
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "ls":
            return ls.run(args)
        elif args.command == "register":
            return register.run(args)
        elif args.command == "info":
            return info.run(args)
        elif args.command == "schema":
            return schema.run(args)
        elif args.command == "head":
            return head.run(args)
        elif args.command == "stream":
            return stream.run(args)
        elif args.command == "inspect":
            return inspect.run(args)
        elif args.command == "cat":
            return cat.run(args)
        elif args.command == "cache":
            if args.cache_command is None:
                print("usage: warpdata cache {status,gc,clear}", file=sys.stderr)
                return 1
            return cache.run(args)
        elif args.command == "warm":
            return warm.run(args)
        elif args.command == "publish":
            return publish.run(args)
        elif args.command == "init":
            return init.run(args)
        elif args.command == "doctor":
            return doctor.run(args)
        elif args.command == "embeddings":
            if args.embeddings_command is None:
                print("usage: warpdata embeddings {list,add,info,publish}", file=sys.stderr)
                return 1
            return embeddings.run(args)
        elif args.command == "ingest":
            if args.ingest_command is None:
                print("usage: warpdata ingest {imagefolder,paired,csv}", file=sys.stderr)
                return 1
            return ingest.run(args)
        elif args.command == "sync":
            return sync.run(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
