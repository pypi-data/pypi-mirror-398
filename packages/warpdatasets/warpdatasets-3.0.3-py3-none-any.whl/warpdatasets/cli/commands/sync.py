"""Sync command - push/pull manifests to/from S3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def run(args: argparse.Namespace) -> int:
    """Run sync command."""
    subcommand = getattr(args, "sync_command", None)

    if subcommand == "push":
        return _run_push(args)
    elif subcommand == "pull":
        return _run_pull(args)
    elif subcommand == "status":
        return _run_status(args)
    else:
        print("Usage: warpdata sync {push|pull|status}")
        print("\nSubcommands:")
        print("  push    Upload local manifests to S3")
        print("  pull    Download manifests from S3 to local")
        print("  status  Show sync status between local and S3")
        return 1


def _get_s3_client():
    """Get boto3 S3 client."""
    try:
        import boto3
    except ImportError:
        print("Error: boto3 is required for S3 sync. Install with: pip install boto3", file=sys.stderr)
        sys.exit(1)
    return boto3.client("s3")


def _get_bucket_and_prefix(args) -> tuple[str, str]:
    """Get S3 bucket and prefix from args or defaults."""
    bucket = getattr(args, "bucket", None) or "warpbucket-warp"
    prefix = getattr(args, "prefix", None) or "warp/manifests"
    return bucket, prefix


def _get_workspace_root(args) -> Path:
    """Get workspace root from args or settings."""
    if hasattr(args, "workspace_root") and args.workspace_root:
        return Path(args.workspace_root)

    from warpdatasets.config.settings import get_settings
    settings = get_settings()
    return Path(settings.workspace_root)


def _list_local_manifests(workspace_root: Path) -> dict[str, dict]:
    """List local manifests with their versions.

    Returns:
        Dict mapping dataset_id to {version, path, size}
    """
    manifests = {}
    manifest_dir = workspace_root / "manifests"

    if not manifest_dir.exists():
        return manifests

    for workspace_path in manifest_dir.iterdir():
        if not workspace_path.is_dir():
            continue
        workspace = workspace_path.name

        for dataset_path in workspace_path.iterdir():
            if not dataset_path.is_dir():
                continue
            name = dataset_path.name
            dataset_id = f"{workspace}/{name}"

            # Read latest.json
            latest_path = dataset_path / "latest.json"
            if not latest_path.exists():
                continue

            try:
                with open(latest_path) as f:
                    latest = json.load(f)
                version = latest.get("version")
                if not version:
                    continue

                manifest_path = dataset_path / f"{version}.json"
                if manifest_path.exists():
                    manifests[dataset_id] = {
                        "version": version,
                        "path": manifest_path,
                        "size": manifest_path.stat().st_size,
                    }
            except Exception:
                continue

    return manifests


def _list_s3_manifests(s3, bucket: str, prefix: str) -> dict[str, dict]:
    """List S3 manifests with their versions.

    Returns:
        Dict mapping dataset_id to {version, key, size}
    """
    manifests = {}
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix + "/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]

            # Skip non-latest.json
            if not key.endswith("/latest.json"):
                continue

            # Parse: prefix/workspace/name/latest.json
            rel_key = key[len(prefix) + 1:]  # Remove prefix/
            parts = rel_key.split("/")
            if len(parts) != 3:
                continue

            workspace, name, _ = parts
            dataset_id = f"{workspace}/{name}"

            # Fetch latest.json to get version
            try:
                response = s3.get_object(Bucket=bucket, Key=key)
                latest = json.loads(response["Body"].read().decode("utf-8"))
                version = latest.get("version") or latest.get("version_hash")
                if not version:
                    continue

                # Get manifest size
                manifest_key = f"{prefix}/{workspace}/{name}/{version}.json"
                try:
                    head = s3.head_object(Bucket=bucket, Key=manifest_key)
                    size = head.get("ContentLength", 0)
                except Exception:
                    size = 0

                manifests[dataset_id] = {
                    "version": version,
                    "key": manifest_key,
                    "size": size,
                }
            except Exception:
                continue

    return manifests


def _run_status(args: argparse.Namespace) -> int:
    """Show sync status."""
    s3 = _get_s3_client()
    bucket, prefix = _get_bucket_and_prefix(args)
    workspace_root = _get_workspace_root(args)

    print(f"Comparing local ({workspace_root}) with S3 (s3://{bucket}/{prefix}/)...\n")

    local = _list_local_manifests(workspace_root)
    remote = _list_s3_manifests(s3, bucket, prefix)

    all_datasets = sorted(set(local.keys()) | set(remote.keys()))

    local_only = []
    remote_only = []
    synced = []
    different = []

    for ds in all_datasets:
        in_local = ds in local
        in_remote = ds in remote

        if in_local and not in_remote:
            local_only.append(ds)
        elif in_remote and not in_local:
            remote_only.append(ds)
        elif local[ds]["version"] == remote[ds]["version"]:
            synced.append(ds)
        else:
            different.append((ds, local[ds]["version"], remote[ds]["version"]))

    if synced:
        print(f"Synced ({len(synced)}):")
        for ds in synced[:10]:
            print(f"  {ds}")
        if len(synced) > 10:
            print(f"  ... and {len(synced) - 10} more")
        print()

    if local_only:
        print(f"Local only ({len(local_only)}) - use 'sync push' to upload:")
        for ds in local_only:
            print(f"  {ds} (v{local[ds]['version'][:8]})")
        print()

    if remote_only:
        print(f"Remote only ({len(remote_only)}) - use 'sync pull' to download:")
        for ds in remote_only:
            print(f"  {ds} (v{remote[ds]['version'][:8]})")
        print()

    if different:
        print(f"Different versions ({len(different)}):")
        for ds, local_v, remote_v in different:
            print(f"  {ds}: local={local_v[:8]} remote={remote_v[:8]}")
        print()

    print(f"Summary: {len(synced)} synced, {len(local_only)} local-only, {len(remote_only)} remote-only, {len(different)} different")
    return 0


def _run_push(args: argparse.Namespace) -> int:
    """Push local manifests to S3."""
    s3 = _get_s3_client()
    bucket, prefix = _get_bucket_and_prefix(args)
    workspace_root = _get_workspace_root(args)

    local = _list_local_manifests(workspace_root)

    if not local:
        print("No local manifests found.")
        return 0

    # Filter by dataset if specified
    if hasattr(args, "dataset") and args.dataset:
        if args.dataset not in local:
            print(f"Dataset not found locally: {args.dataset}", file=sys.stderr)
            return 1
        local = {args.dataset: local[args.dataset]}

    # Get remote to check what needs updating
    remote = _list_s3_manifests(s3, bucket, prefix)

    to_push = []
    for ds, info in local.items():
        if ds not in remote or remote[ds]["version"] != info["version"]:
            to_push.append((ds, info))

    if not to_push:
        print("All manifests already synced.")
        return 0

    print(f"Pushing {len(to_push)} manifest(s) to s3://{bucket}/{prefix}/...\n")

    pushed = 0
    for ds, info in to_push:
        workspace, name = ds.split("/", 1)
        version = info["version"]

        # Read manifest
        with open(info["path"]) as f:
            manifest_data = f.read()

        # Upload manifest
        manifest_key = f"{prefix}/{workspace}/{name}/{version}.json"
        s3.put_object(
            Bucket=bucket,
            Key=manifest_key,
            Body=manifest_data.encode("utf-8"),
            ContentType="application/json",
        )

        # Upload latest.json
        latest_key = f"{prefix}/{workspace}/{name}/latest.json"
        latest_data = json.dumps({"version": version})
        s3.put_object(
            Bucket=bucket,
            Key=latest_key,
            Body=latest_data.encode("utf-8"),
            ContentType="application/json",
        )

        print(f"  {ds} (v{version[:8]})")
        pushed += 1

    print(f"\nPushed {pushed} manifest(s)")
    return 0


def _run_pull(args: argparse.Namespace) -> int:
    """Pull manifests from S3.

    If --data is specified, also downloads data shards into the local mirror.
    """
    s3 = _get_s3_client()
    bucket, prefix = _get_bucket_and_prefix(args)
    workspace_root = _get_workspace_root(args)

    # Check if we should also pull data
    pull_data = getattr(args, "data", False)

    remote = _list_s3_manifests(s3, bucket, prefix)

    if not remote:
        print("No remote manifests found.")
        return 0

    # Filter by dataset if specified
    if hasattr(args, "dataset") and args.dataset:
        if args.dataset not in remote:
            print(f"Dataset not found on S3: {args.dataset}", file=sys.stderr)
            return 1
        remote = {args.dataset: remote[args.dataset]}

    # Get local to check what needs updating
    local = _list_local_manifests(workspace_root)

    to_pull = []
    for ds, info in remote.items():
        if ds not in local or local[ds]["version"] != info["version"]:
            to_pull.append((ds, info))

    if not to_pull:
        print("All manifests already synced.")
        if pull_data:
            # Still need to check for missing data shards
            for ds, info in remote.items():
                _pull_data_shards(s3, bucket, prefix, workspace_root, ds, info["version"])
        return 0

    print(f"Pulling {len(to_pull)} manifest(s) from s3://{bucket}/{prefix}/...\n")

    pulled = 0
    for ds, info in to_pull:
        workspace, name = ds.split("/", 1)
        version = info["version"]

        # Create local directory
        manifest_dir = workspace_root / "manifests" / workspace / name
        manifest_dir.mkdir(parents=True, exist_ok=True)

        # Download manifest
        manifest_key = info["key"]
        response = s3.get_object(Bucket=bucket, Key=manifest_key)
        manifest_data = response["Body"].read().decode("utf-8")

        # Write manifest
        manifest_path = manifest_dir / f"{version}.json"
        with open(manifest_path, "w") as f:
            f.write(manifest_data)

        # Write latest.json
        latest_path = manifest_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump({"version": version}, f)

        print(f"  {ds} (v{version[:8]})")
        pulled += 1

        # Pull data shards if requested
        if pull_data:
            _pull_data_shards(s3, bucket, prefix, workspace_root, ds, version)

    print(f"\nPulled {pulled} manifest(s)")
    return 0


def _pull_data_shards(
    s3,
    bucket: str,
    prefix: str,
    workspace_root: Path,
    dataset_id: str,
    version: str,
) -> None:
    """Pull data shards for a dataset into the local mirror.

    Downloads shards from S3 to:
        workspace_root/data/{workspace}/{name}/{version}/...

    This creates a local mirror matching the remote layout.
    """
    from warpdatasets.manifest.model import Manifest

    workspace, name = dataset_id.split("/", 1)

    # Load manifest
    manifest_path = workspace_root / "manifests" / workspace / name / f"{version}.json"
    if not manifest_path.exists():
        print(f"    Warning: Manifest not found for {dataset_id}, skipping data pull")
        return

    with open(manifest_path) as f:
        manifest_data = json.load(f)

    manifest = Manifest.from_dict(manifest_data)

    # Compute data prefix on S3
    # Extract from manifest.locations or derive from base prefix
    data_prefix = prefix.replace("/manifests", "/data")
    data_base = f"{data_prefix}/{workspace}/{name}/{version}"

    # Create local data directory
    local_data_base = workspace_root / "data" / workspace / name / version
    local_data_base.mkdir(parents=True, exist_ok=True)

    # Track shards to download
    shards_to_download = []

    # Collect table shards
    for table_name, table in manifest.tables.items():
        for shard in table.shards:
            if shard.key:
                key = shard.key
            elif shard.uri and shard.uri.startswith("s3://"):
                # Extract key from legacy S3 URI
                parts = shard.uri.split("/", 3)
                if len(parts) >= 4:
                    key = parts[3].split(version + "/", 1)[-1] if version in parts[3] else None
                else:
                    continue
            else:
                continue

            if key:
                s3_key = f"{data_base}/{key}"
                local_path = local_data_base / key
                if not local_path.exists():
                    shards_to_download.append((s3_key, local_path, shard.byte_size))

    # Collect artifact shards
    for artifact_name, artifact in manifest.artifacts.items():
        for shard in artifact.shards:
            if shard.key:
                key = shard.key
                s3_key = f"{data_base}/{key}"
                local_path = local_data_base / key
                if not local_path.exists():
                    shards_to_download.append((s3_key, local_path, shard.byte_size))

        # Collect index if present
        if artifact.index:
            if artifact.index.key:
                key = artifact.index.key
                s3_key = f"{data_base}/{key}"
                local_path = local_data_base / key
                if not local_path.exists():
                    shards_to_download.append((s3_key, local_path, artifact.index.byte_size))

    if not shards_to_download:
        print(f"    All data shards for {dataset_id} already present")
        return

    total_bytes = sum(size or 0 for _, _, size in shards_to_download)
    total_mb = total_bytes / (1024 * 1024)
    print(f"    Downloading {len(shards_to_download)} shard(s) ({total_mb:.1f} MB) for {dataset_id}...")

    downloaded = 0
    for s3_key, local_path, _ in shards_to_download:
        try:
            # Create parent directory
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download
            s3.download_file(bucket, s3_key, str(local_path))
            downloaded += 1
        except Exception as e:
            print(f"    Warning: Failed to download {s3_key}: {e}")

    print(f"    Downloaded {downloaded}/{len(shards_to_download)} shard(s)")
