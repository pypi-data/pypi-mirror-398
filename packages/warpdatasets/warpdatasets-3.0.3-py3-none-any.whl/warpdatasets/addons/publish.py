"""Addon publishing - upload addons to remote storage.

Supports uploading addon data (vectors, indexes) to S3 or other storage
and updating manifests with remote URIs.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from warpdatasets.manifest.model import AddonDescriptor, Manifest, ShardInfo


def publish_addon(
    addon: "AddonDescriptor",
    addon_name: str,
    dataset_id: str,
    dataset_version: str,
    base_uri: str,
    *,
    force: bool = False,
    dry_run: bool = False,
    progress: bool = True,
) -> "AddonDescriptor":
    """Publish an addon to remote storage.

    Uploads addon files and returns a new AddonDescriptor with remote URIs.

    Args:
        addon: Local addon descriptor
        addon_name: Name of the addon
        dataset_id: Dataset ID (workspace/name)
        dataset_version: Dataset version hash
        base_uri: Base URI for storage (e.g., "s3://bucket/warp")
        force: Overwrite existing files
        dry_run: Show what would be done without uploading
        progress: Show progress bar

    Returns:
        New AddonDescriptor with remote URIs
    """
    from warpdatasets.manifest.model import (
        AddonDescriptor,
        TableDescriptor,
        ShardInfo,
        IndexDescriptor,
    )

    parsed = urlparse(base_uri)

    if parsed.scheme == "s3":
        uploader = S3Uploader(
            bucket=parsed.netloc,
            prefix=parsed.path.lstrip("/"),
            force=force,
            dry_run=dry_run,
            progress=progress,
        )
    elif parsed.scheme in ("file", "") or not parsed.scheme:
        # Local file system
        uploader = LocalUploader(
            base_path=Path(parsed.path if parsed.scheme == "file" else base_uri),
            force=force,
            dry_run=dry_run,
        )
    else:
        raise ValueError(f"Unsupported storage scheme: {parsed.scheme}")

    # Build remote path prefix
    workspace, name = dataset_id.split("/", 1)
    addon_path = f"data/{workspace}/{name}/{dataset_version[:12]}/addons/{_sanitize_addon_name(addon_name)}"

    # Upload vectors table
    new_vectors = None
    if addon.vectors:
        new_shards = []
        for i, shard in enumerate(addon.vectors.shards):
            local_path = _resolve_local_path(shard.uri)
            remote_uri = uploader.upload(
                local_path,
                f"{addon_path}/vectors/shard-{i:05d}.parquet",
            )
            new_shards.append(ShardInfo(
                uri=remote_uri,
                hash=shard.hash,
                row_count=shard.row_count,
                byte_size=shard.byte_size,
            ))

        new_vectors = TableDescriptor(
            format=addon.vectors.format,
            shards=new_shards,
            schema=addon.vectors.schema,
            row_count=addon.vectors.row_count,
        )

    # Upload index if present
    new_index = None
    if addon.index:
        local_path = _resolve_local_path(addon.index.uri)
        remote_uri = uploader.upload(
            local_path,
            f"{addon_path}/index.faiss",
        )
        new_index = IndexDescriptor(
            kind=addon.index.kind,
            uri=remote_uri,
            byte_size=addon.index.byte_size,
            meta=addon.index.meta,
        )

    # Create new descriptor with remote URIs
    return AddonDescriptor(
        kind=addon.kind,
        base_table=addon.base_table,
        key=addon.key,
        vectors=new_vectors,
        params=addon.params,
        index=new_index,
        meta=addon.meta,
    )


def _sanitize_addon_name(name: str) -> str:
    """Sanitize addon name for use in paths."""
    return name.replace(":", "--").replace("@", "--")


def _resolve_local_path(uri: str) -> Path:
    """Resolve a URI to a local path."""
    if uri.startswith("file://"):
        return Path(uri[7:])
    elif "://" not in uri:
        return Path(uri)
    else:
        raise ValueError(f"Cannot resolve non-local URI: {uri}")


class LocalUploader:
    """Uploader for local file system."""

    def __init__(
        self,
        base_path: Path,
        force: bool = False,
        dry_run: bool = False,
    ):
        self.base_path = base_path
        self.force = force
        self.dry_run = dry_run

    def upload(self, local_path: Path, remote_key: str) -> str:
        """Copy file to destination."""
        dest_path = self.base_path / remote_key
        dest_uri = str(dest_path)

        if self.dry_run:
            print(f"Would copy: {local_path} -> {dest_path}")
            return dest_uri

        if dest_path.exists() and not self.force:
            print(f"Exists: {dest_path}")
            return dest_uri

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(local_path, dest_path)

        return dest_uri


class S3Uploader:
    """Uploader for S3."""

    def __init__(
        self,
        bucket: str,
        prefix: str,
        force: bool = False,
        dry_run: bool = False,
        progress: bool = True,
    ):
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.force = force
        self.dry_run = dry_run
        self.progress = progress

        if not dry_run:
            try:
                import boto3
                self.s3 = boto3.client("s3")
            except ImportError:
                raise ImportError("boto3 required for S3 uploads: pip install boto3")

    def upload(self, local_path: Path, remote_key: str) -> str:
        """Upload file to S3."""
        full_key = f"{self.prefix}/{remote_key}" if self.prefix else remote_key
        remote_uri = f"s3://{self.bucket}/{full_key}"

        if self.dry_run:
            print(f"Would upload: {local_path} -> {remote_uri}")
            return remote_uri

        # Check if exists
        if not self.force:
            try:
                self.s3.head_object(Bucket=self.bucket, Key=full_key)
                print(f"Exists: {remote_uri}")
                return remote_uri
            except self.s3.exceptions.ClientError:
                pass  # Object doesn't exist, proceed with upload

        # Upload with progress
        file_size = local_path.stat().st_size

        if self.progress and file_size > 1024 * 1024:  # Show progress for files > 1MB
            try:
                from tqdm import tqdm

                with tqdm(total=file_size, unit="B", unit_scale=True, desc=local_path.name) as pbar:
                    self.s3.upload_file(
                        str(local_path),
                        self.bucket,
                        full_key,
                        Callback=lambda bytes_transferred: pbar.update(bytes_transferred),
                    )
            except ImportError:
                self.s3.upload_file(str(local_path), self.bucket, full_key)
        else:
            self.s3.upload_file(str(local_path), self.bucket, full_key)

        return remote_uri


def update_manifest_with_addon(
    manifest: "Manifest",
    addon_name: str,
    addon: "AddonDescriptor",
) -> "Manifest":
    """Create a new manifest with the addon added/updated.

    Args:
        manifest: Original manifest
        addon_name: Name for the addon
        addon: Addon descriptor to add

    Returns:
        New manifest with the addon
    """
    from warpdatasets.manifest.model import Manifest

    new_addons = dict(manifest.addons)
    new_addons[addon_name] = addon

    return Manifest(
        dataset=manifest.dataset,
        tables=manifest.tables,
        artifacts=manifest.artifacts,
        bindings=manifest.bindings,
        addons=new_addons,
        schema=manifest.schema,
        row_count=manifest.row_count,
        meta=manifest.meta,
    )


def save_manifest(
    manifest: "Manifest",
    output_path: Path | str,
) -> None:
    """Save manifest to file.

    Args:
        manifest: Manifest to save
        output_path: Output path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(manifest.to_dict(), f, indent=2)
