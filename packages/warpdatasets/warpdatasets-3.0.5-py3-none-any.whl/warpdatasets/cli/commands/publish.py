"""Publish CLI command."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _normalize_ref_value(v: str | None, artifact_root: Path) -> str | None:
    """Convert absolute path to relative tar member path.

    Args:
        v: Original ref value (may be absolute path)
        artifact_root: Root directory of the artifact

    Returns:
        Relative path suitable for tar member lookup
    """
    if v is None:
        return None
    v = str(v)

    # Normalize separators early
    v_norm = v.replace("\\", "/")

    # If absolute path, make relative to artifact root
    if os.path.isabs(v_norm):
        p = Path(v_norm).resolve()
        root = artifact_root.resolve()
        try:
            rel = p.relative_to(root)
        except ValueError:
            raise ValueError(
                f"Ref value points outside artifact root.\n"
                f"  value: {v}\n"
                f"  artifact_root: {artifact_root}"
            )
        return rel.as_posix()

    # Already relative → keep but normalize
    return Path(v_norm).as_posix().lstrip("./")


def _rewrite_parquet_ref_columns(
    parquet_path: Path,
    column_to_root: dict[str, Path],
    output_path: Path,
) -> None:
    """Rewrite ref columns in parquet to use relative paths.

    Args:
        parquet_path: Source parquet file
        column_to_root: Mapping of column name to artifact root
        output_path: Destination for rewritten parquet
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pq.read_table(parquet_path)

    for col, root in column_to_root.items():
        if col not in table.column_names:
            continue
        values = table[col].to_pylist()
        new_values = [_normalize_ref_value(v, root) for v in values]
        idx = table.schema.get_field_index(col)
        table = table.set_column(idx, col, pa.array(new_values, type=pa.string()))

    pq.write_table(table, output_path)


def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes."""
    size_str = size_str.strip().upper()

    multipliers = {
        "B": 1,
        "KB": 1024,
        "K": 1024,
        "MB": 1024 * 1024,
        "M": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "G": 1024 * 1024 * 1024,
    }

    for suffix, mult in multipliers.items():
        if size_str.endswith(suffix):
            num_str = size_str[: -len(suffix)].strip()
            return int(float(num_str) * mult)

    return int(size_str)


def parse_binding(binding_str: str) -> tuple[str, str, str, str, str]:
    """Parse a binding string.

    Format: table.column=artifact:media_type:ref_type

    Returns:
        (table, column, artifact, media_type, ref_type)
    """
    if "=" not in binding_str:
        raise ValueError(f"Invalid binding format: {binding_str}")

    left, right = binding_str.split("=", 1)

    if "." not in left:
        raise ValueError(f"Invalid binding format (need table.column): {binding_str}")

    table, column = left.split(".", 1)

    parts = right.split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid binding format (need artifact:media_type): {binding_str}")

    artifact = parts[0]
    media_type = parts[1]
    ref_type = parts[2] if len(parts) > 2 else "tar_member_path"

    return table, column, artifact, media_type, ref_type


def _publish_existing_dataset(args: argparse.Namespace, settings, base_uri: str) -> int:
    """Publish an existing local dataset to S3.

    This uploads local files to S3 and rewrites the manifest with S3 URIs.
    """
    import hashlib
    import json
    import boto3

    dataset_id = args.dataset

    # Load existing manifest
    manifest_dir = settings.workspace_root / "manifests"
    workspace, name = dataset_id.split("/", 1)
    dataset_manifest_dir = manifest_dir / workspace / name

    latest_path = dataset_manifest_dir / "latest.json"
    if not latest_path.exists():
        print(f"Error: Dataset '{dataset_id}' not found locally", file=sys.stderr)
        print(f"Expected manifest at: {dataset_manifest_dir}", file=sys.stderr)
        return 1

    with open(latest_path) as f:
        latest = json.load(f)
    version = latest["version"]

    manifest_path = dataset_manifest_dir / f"{version}.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"Publishing existing dataset: {dataset_id}")
    print(f"  Version: {version[:12]}")
    print(f"  Destination: {base_uri}")

    # Parse S3 bucket/prefix from base_uri
    if not base_uri.startswith("s3://"):
        print(f"Error: Only S3 publishing is supported. Got: {base_uri}", file=sys.stderr)
        return 1

    from urllib.parse import urlparse
    parsed = urlparse(base_uri)
    bucket = parsed.netloc
    base_prefix = parsed.path.lstrip("/")
    objects_prefix = f"{base_prefix}/objects" if base_prefix else "objects"

    s3 = boto3.client("s3")

    def upload_file_to_s3(local_path: Path, content_type: str = "application/octet-stream") -> str:
        """Upload a file to S3 with content-addressable path. Returns S3 URI."""
        from tqdm import tqdm

        # Compute SHA256 hash
        file_size = local_path.stat().st_size
        sha256 = hashlib.sha256()
        with open(local_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_hash = sha256.hexdigest()

        # S3 key: objects/ab/cd/abcd1234...
        s3_key = f"{objects_prefix}/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}"
        s3_uri = f"s3://{bucket}/{s3_key}"

        # Check if already exists
        try:
            s3.head_object(Bucket=bucket, Key=s3_key)
            size_mb = file_size / (1024 * 1024)
            print(f"    [skip] {local_path.name} ({size_mb:.1f} MB, already exists)")
            return s3_uri
        except s3.exceptions.ClientError:
            pass

        # Upload with progress bar
        size_mb = file_size / (1024 * 1024)

        class ProgressCallback:
            def __init__(self, total_size, filename):
                self.pbar = tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"    {filename[:40]}",
                    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]'
                )

            def __call__(self, bytes_transferred):
                self.pbar.update(bytes_transferred)

            def close(self):
                self.pbar.close()

        callback = ProgressCallback(file_size, local_path.name)
        try:
            s3.upload_file(
                str(local_path),
                bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type},
                Callback=callback,
            )
        finally:
            callback.close()

        return s3_uri

    def resolve_local_path(uri: str) -> Path | None:
        """Resolve a local:// or file:// URI to a Path."""
        if uri.startswith("local://"):
            rel_path = uri[8:]
            return settings.workspace_root / rel_path
        elif uri.startswith("file://"):
            return Path(uri[7:])
        return None

    # Build mapping: artifact_name -> local root dir (only for directory artifacts)
    artifact_roots: dict[str, Path] = {}
    for artifact_name, artifact_data in manifest.get("artifacts", {}).items():
        if artifact_data.get("kind") != "directory":
            continue
        if not artifact_data.get("shards"):
            continue
        base_uri = artifact_data["shards"][0]["uri"]
        local_root = resolve_local_path(base_uri)
        if local_root and local_root.exists() and local_root.is_dir():
            artifact_roots[artifact_name] = local_root

    # Determine which table columns must be rewritten: column -> artifact_root
    column_to_root: dict[str, Path] = {}
    for b in manifest.get("bindings", []):
        # Only rewrite columns bound to directory artifacts we are converting
        art = b["artifact"]
        if art in artifact_roots:
            column_to_root[b["column"]] = artifact_roots[art]

    # Rewrite parquet shards locally (only if needed)
    rewritten_parquet: dict[str, list[Path]] = {}  # table_name -> rewritten shard paths
    tmp_dir = None

    if column_to_root:
        import tempfile
        tmp_dir = Path(tempfile.mkdtemp(prefix="warpdata_rewrite_"))
        print(f"\nRewriting ref columns: {list(column_to_root.keys())}")

        for table_name, table_data in manifest.get("tables", {}).items():
            new_paths = []
            for i, shard in enumerate(table_data.get("shards", [])):
                uri = shard.get("uri") or shard.get("key")
                local_path = resolve_local_path(uri) if uri else None

                if not local_path or not local_path.exists():
                    # If it's already remote and you can't rewrite, error
                    raise RuntimeError(f"Cannot rewrite refs; shard not local: {uri}")

                out_path = tmp_dir / f"{table_name}--shard-{i:05d}.parquet"
                _rewrite_parquet_ref_columns(local_path, column_to_root, out_path)
                new_paths.append(out_path)
                print(f"    Rewrote {local_path.name}")

            rewritten_parquet[table_name] = new_paths

    # Upload table shards
    print("\nUploading table shards...")
    new_tables = {}
    for table_name, table_data in manifest.get("tables", {}).items():
        new_shards = []
        for i, shard in enumerate(table_data.get("shards", [])):
            uri = shard.get("uri") or shard.get("key")

            # Use rewritten parquet if available
            if table_name in rewritten_parquet:
                local_path = rewritten_parquet[table_name][i]
            else:
                local_path = resolve_local_path(uri) if uri else None

            if local_path and local_path.exists():
                new_uri = upload_file_to_s3(local_path, "application/octet-stream")
                new_shards.append({**shard, "uri": new_uri})
            elif uri and uri.startswith("s3://"):
                # Already on S3
                new_shards.append(shard)
            else:
                print(f"    [warn] Cannot resolve: {uri}", file=sys.stderr)
                new_shards.append(shard)

        new_tables[table_name] = {**table_data, "shards": new_shards}

    # Upload artifacts (if they have local paths)
    print("\nUploading artifacts...")
    new_artifacts = {}
    for artifact_name, artifact_data in manifest.get("artifacts", {}).items():
        kind = artifact_data.get("kind", "")

        if kind == "directory":
            # Need to pack directory into tar and upload
            new_shards = []
            all_tar_paths = []  # Collect for index building
            for shard in artifact_data.get("shards", []):
                uri = shard.get("uri") or shard.get("key")
                local_path = resolve_local_path(uri) if uri else None

                if local_path and local_path.exists() and local_path.is_dir():
                    # Pack directory to tar
                    print(f"    Packing {artifact_name} from {local_path}...")
                    from warpdatasets.publish.packer import pack_directory_to_tar_shards

                    tar_output = Path("/tmp") / f".warp_tar_{artifact_name}"
                    tar_shards = pack_directory_to_tar_shards(
                        local_path,
                        output_dir=tar_output,
                        shard_size_bytes=4 * 1024 * 1024 * 1024,  # 4GB shards
                    )

                    # Upload tar shards
                    for tar_shard in tar_shards:
                        tar_uri = upload_file_to_s3(tar_shard.path, "application/x-tar")
                        new_shards.append({
                            "uri": tar_uri,
                            "byte_size": tar_shard.size_bytes,
                        })
                        all_tar_paths.append(tar_shard.path)
                else:
                    new_shards.append(shard)

            # Build artifact index for tar shards
            index_info = None
            if all_tar_paths:
                import tempfile
                from warpdatasets.artifacts.tar.index_builder import build_tar_index, write_index_parquet

                print(f"    Building index for {artifact_name}...")
                entries = build_tar_index(all_tar_paths)

                index_tmp_dir = Path(tempfile.mkdtemp(prefix="warpdata_art_index_"))
                index_path = index_tmp_dir / f"{artifact_name}_index.parquet"
                write_index_parquet(entries, index_path)

                # Upload index
                index_uri = upload_file_to_s3(index_path, "application/octet-stream")
                index_info = {
                    "uri": index_uri,
                    "byte_size": index_path.stat().st_size,
                }

                # Clean up index temp file
                index_path.unlink()
                index_tmp_dir.rmdir()

            # Clean up temp tar files
            for tar_path in all_tar_paths:
                if tar_path.exists():
                    tar_path.unlink()

            # Change kind from directory to tar_shards, include index
            artifact_dict = {
                "kind": "tar_shards",
                "shards": new_shards,
            }
            if index_info:
                artifact_dict["index"] = index_info
            new_artifacts[artifact_name] = artifact_dict

        elif kind in ("tar", "tar_shards"):
            # Already tar, just upload if local
            new_shards = []
            for shard in artifact_data.get("shards", []):
                uri = shard.get("uri") or shard.get("key")
                local_path = resolve_local_path(uri) if uri else None

                if local_path and local_path.exists():
                    new_uri = upload_file_to_s3(local_path, "application/x-tar")
                    new_shards.append({**shard, "uri": new_uri})
                elif uri and uri.startswith("s3://"):
                    new_shards.append(shard)
                else:
                    new_shards.append(shard)

            new_artifacts[artifact_name] = {**artifact_data, "shards": new_shards}
        else:
            # Unknown kind, keep as is
            new_artifacts[artifact_name] = artifact_data

    # Update bindings to match artifact kind changes (directory -> tar_shards)
    new_bindings = []
    for b in manifest.get("bindings", []):
        art = b["artifact"]
        if art in new_artifacts and new_artifacts[art]["kind"] == "tar_shards":
            # Ensure correct ref_type for tar_shards
            b = {**b, "ref_type": "tar_member_path"}
        new_bindings.append(b)

    # Build new manifest
    new_manifest = {
        **manifest,
        "tables": new_tables,
    }
    if new_artifacts:
        new_manifest["artifacts"] = new_artifacts
    if new_bindings:
        new_manifest["bindings"] = new_bindings

    # Compute new version hash
    manifest_json = json.dumps(new_manifest, sort_keys=True, separators=(",", ":"))
    new_version = hashlib.sha256(manifest_json.encode()).hexdigest()[:12]

    print(f"\nNew version: {new_version}")

    # Save new manifest locally
    new_manifest_path = dataset_manifest_dir / f"{new_version}.json"
    with open(new_manifest_path, "w") as f:
        json.dump(new_manifest, f, indent=2)

    # Update latest.json
    with open(latest_path, "w") as f:
        json.dump({"version": new_version}, f)

    print(f"  Saved local manifest: {new_manifest_path}")

    # Push to S3 manifests
    manifests_prefix = f"{base_prefix}/manifests" if base_prefix else "manifests"

    manifest_s3_key = f"{manifests_prefix}/{workspace}/{name}/{new_version}.json"
    latest_s3_key = f"{manifests_prefix}/{workspace}/{name}/latest.json"

    print(f"\nPushing manifest to S3...")
    s3.put_object(
        Bucket=bucket,
        Key=manifest_s3_key,
        Body=json.dumps(new_manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    print(f"  Uploaded: s3://{bucket}/{manifest_s3_key}")

    s3.put_object(
        Bucket=bucket,
        Key=latest_s3_key,
        Body=json.dumps({"version": new_version}).encode("utf-8"),
        ContentType="application/json",
    )
    print(f"  Updated latest pointer")

    print(f"\nPublish complete!")
    print(f"  Dataset: {dataset_id}")
    print(f"  Version: {new_version}")

    return 0


def run(args: argparse.Namespace) -> int:
    """Run publish command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from warpdatasets.publish.builder import ManifestBuilder
    from warpdatasets.publish.packer import pack_directory_to_tar_shards
    from warpdatasets.publish.storage import create_storage
    from warpdatasets.publish.uploader import Uploader
    from warpdatasets.publish.verify import verify_publish
    from warpdatasets.config.settings import get_settings

    settings = get_settings()

    # Get base URI - use default S3 bucket if not specified
    base_uri = args.base_uri or settings.manifest_base
    if not base_uri:
        # Use default warp bucket
        from warpdatasets.config.settings import DEFAULT_MANIFEST_BASE
        base_uri = DEFAULT_MANIFEST_BASE

    # Check if this is publishing an existing local dataset (no --table specified)
    if not args.table:
        return _publish_existing_dataset(args, settings, base_uri)

    # Parse table inputs
    table_inputs = {}
    if args.table:
        for table_spec in args.table:
            if "=" not in table_spec:
                print(f"Error: Invalid table format: {table_spec}", file=sys.stderr)
                print("Expected: name=path/to/shards/*.parquet", file=sys.stderr)
                return 1

            name, pattern = table_spec.split("=", 1)

            # Expand glob pattern
            base_path = Path(pattern).parent
            glob_pattern = Path(pattern).name
            shard_paths = list(base_path.glob(glob_pattern))

            if not shard_paths:
                print(f"Error: No files found matching: {pattern}", file=sys.stderr)
                return 1

            table_inputs[name] = shard_paths

    if not table_inputs:
        print("Error: At least one --table is required", file=sys.stderr)
        return 1

    # Parse artifact inputs
    artifact_dirs = {}
    if args.artifact:
        for artifact_spec in args.artifact:
            if "=" not in artifact_spec:
                print(f"Error: Invalid artifact format: {artifact_spec}", file=sys.stderr)
                print("Expected: name=path/to/directory", file=sys.stderr)
                return 1

            name, dir_path = artifact_spec.split("=", 1)
            artifact_dirs[name] = Path(dir_path)

            if not artifact_dirs[name].is_dir():
                print(f"Error: Artifact directory not found: {dir_path}", file=sys.stderr)
                return 1

    # Parse bindings
    bindings = []
    if args.bind:
        for bind_str in args.bind:
            try:
                bindings.append(parse_binding(bind_str))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

    # Parse shard size
    shard_size = parse_size(args.shard_size)

    print(f"Publishing: {args.dataset}")
    print(f"Base URI: {base_uri}")

    # Build manifest
    builder = ManifestBuilder(
        dataset_id=args.dataset,
        base_uri=base_uri,
    )

    # Add tables
    for name, shard_paths in table_inputs.items():
        print(f"  Table '{name}': {len(shard_paths)} shards")
        builder.add_table(name, shard_paths)

    # Pack and add artifacts
    artifact_shards = {}
    for name, dir_path in artifact_dirs.items():
        print(f"  Packing artifact '{name}' from {dir_path}...")

        tar_output = Path(args.temp_dir or ".") / f".warp_tar_{name}"
        shards = pack_directory_to_tar_shards(
            dir_path,
            output_dir=tar_output,
            shard_size_bytes=shard_size,
        )

        print(f"    -> {len(shards)} tar shards")
        artifact_shards[name] = shards
        builder.add_artifact(name, shards)

    # Add bindings
    for table, column, artifact, media_type, ref_type in bindings:
        print(f"  Binding: {table}.{column} -> {artifact}:{media_type}")
        builder.add_binding(table, column, artifact, media_type, ref_type)

    # Build plan
    plan = builder.build_plan()

    print()
    print(f"Version hash: {plan.manifest.version_hash}")
    print(f"Total shards: {plan.shard_count}")
    print(f"Total bytes: {plan._format_bytes(plan.total_bytes)}")

    if args.dry_run:
        print()
        print("DRY RUN - would upload:")
        for upload in plan.all_uploads:
            print(f"  {upload.source_path.name} -> {upload.target_uri}")
        print(f"  manifest -> {plan.manifest_uri}")
        if args.set_latest:
            print(f"  latest -> {plan.latest_uri}")
        return 0

    # Create storage and uploader
    storage = create_storage(
        base_uri,
        region=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
    )

    uploader = Uploader(
        storage=storage,
        concurrency=args.concurrency,
    )

    # Execute publish
    print()
    print("Uploading...")

    result = uploader.execute_plan(
        plan,
        skip_existing=not args.force,
        update_latest=args.set_latest,
    )

    if not result.success:
        print()
        print("Publish FAILED:", file=sys.stderr)
        for error in result.errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    print()
    print(f"Uploaded: {result.shards_uploaded} shards")
    print(f"Skipped:  {result.shards_skipped} shards (already exist)")

    if result.latest_updated:
        print(f"Updated latest pointer")

    # Verify if requested
    if args.verify:
        print()
        print("Verifying...")
        verify_result = verify_publish(plan, storage, check_schema=True)

        if verify_result.success:
            print("Verification: PASSED")
        else:
            print("Verification: FAILED", file=sys.stderr)
            for error in verify_result.errors:
                print(f"  {error}", file=sys.stderr)
            return 1

    print()
    print("Publish complete!")
    print(f"  Dataset: {args.dataset}")
    print(f"  Version: {result.version_hash}")
    print(f"  Manifest: {result.manifest_uri}")

    return 0
