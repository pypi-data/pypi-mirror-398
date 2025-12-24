"""Uploader for publishing datasets.

Handles transactional upload of shards, manifest, and latest pointer.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from warpdatasets.publish.plan import PublishPlan, UploadItem

logger = logging.getLogger(__name__)


class StorageBackend(Protocol):
    """Protocol for storage backends."""

    def put_object(self, uri: str, data: bytes) -> None:
        """Upload data to a URI."""
        ...

    def put_file(self, uri: str, path: Path) -> None:
        """Upload a file to a URI."""
        ...

    def head_object(self, uri: str) -> dict | None:
        """Get object metadata (None if not found)."""
        ...

    def get_object(self, uri: str) -> bytes | None:
        """Get object content (None if not found)."""
        ...


@dataclass
class UploadResult:
    """Result of an upload operation."""

    uri: str
    success: bool
    skipped: bool = False
    error: str | None = None


@dataclass
class PublishResult:
    """Result of a publish operation."""

    success: bool
    version_hash: str
    manifest_uri: str
    latest_updated: bool
    shards_uploaded: int
    shards_skipped: int
    errors: list[str]


class Uploader:
    """Uploads dataset to storage backend.

    Handles:
    - Idempotent shard uploads (skip if exists with same size)
    - Transactional ordering (shards -> manifest -> latest)
    - Parallel uploads
    """

    def __init__(
        self,
        storage: StorageBackend,
        concurrency: int = 4,
    ):
        """Initialize uploader.

        Args:
            storage: Storage backend for uploads
            concurrency: Number of parallel uploads
        """
        self._storage = storage
        self._concurrency = concurrency

    def execute_plan(
        self,
        plan: PublishPlan,
        skip_existing: bool = True,
        update_latest: bool = True,
        dry_run: bool = False,
    ) -> PublishResult:
        """Execute a publish plan.

        Args:
            plan: The publish plan to execute
            skip_existing: Skip shards that already exist with same size
            update_latest: Whether to update the latest pointer
            dry_run: If True, only log what would be done

        Returns:
            PublishResult with status and statistics
        """
        errors = []
        shards_uploaded = 0
        shards_skipped = 0

        if dry_run:
            logger.info(f"DRY RUN: Would upload {plan.shard_count} shards")
            logger.info(f"DRY RUN: Manifest URI: {plan.manifest_uri}")
            if update_latest:
                logger.info(f"DRY RUN: Latest URI: {plan.latest_uri}")
            return PublishResult(
                success=True,
                version_hash=plan.manifest.version_hash,
                manifest_uri=plan.manifest_uri,
                latest_updated=update_latest,
                shards_uploaded=0,
                shards_skipped=plan.shard_count,
                errors=[],
            )

        # Step 1: Upload shards (parallel)
        logger.info(f"Uploading {plan.shard_count} shards...")

        shard_results = self._upload_shards(
            plan.all_uploads,
            skip_existing=skip_existing,
        )

        for result in shard_results:
            if result.success:
                if result.skipped:
                    shards_skipped += 1
                else:
                    shards_uploaded += 1
            else:
                errors.append(f"Failed to upload {result.uri}: {result.error}")

        # If any shard failed, don't proceed
        if errors:
            logger.error(f"Shard upload failed with {len(errors)} errors")
            return PublishResult(
                success=False,
                version_hash=plan.manifest.version_hash,
                manifest_uri=plan.manifest_uri,
                latest_updated=False,
                shards_uploaded=shards_uploaded,
                shards_skipped=shards_skipped,
                errors=errors,
            )

        logger.info(f"Shards: {shards_uploaded} uploaded, {shards_skipped} skipped")

        # Step 2: Upload manifest
        logger.info(f"Uploading manifest to {plan.manifest_uri}")
        try:
            manifest_json = json.dumps(plan.manifest.to_dict(), indent=2)
            self._storage.put_object(plan.manifest_uri, manifest_json.encode())
        except Exception as e:
            errors.append(f"Failed to upload manifest: {e}")
            return PublishResult(
                success=False,
                version_hash=plan.manifest.version_hash,
                manifest_uri=plan.manifest_uri,
                latest_updated=False,
                shards_uploaded=shards_uploaded,
                shards_skipped=shards_skipped,
                errors=errors,
            )

        # Step 3: Update latest pointer (last)
        latest_updated = False
        if update_latest:
            logger.info(f"Updating latest pointer to {plan.latest_uri}")
            try:
                latest_content = {
                    "version": plan.manifest.version_hash,
                    "manifest": plan.manifest_uri,
                }
                self._storage.put_object(
                    plan.latest_uri,
                    json.dumps(latest_content).encode(),
                )
                latest_updated = True
            except Exception as e:
                errors.append(f"Failed to update latest: {e}")
                # This is not fatal - version is still published

        success = len(errors) == 0
        if success:
            logger.info(f"Published {plan.manifest.dataset} version {plan.manifest.version_hash}")
        else:
            logger.warning(f"Publish completed with {len(errors)} errors")

        return PublishResult(
            success=success,
            version_hash=plan.manifest.version_hash,
            manifest_uri=plan.manifest_uri,
            latest_updated=latest_updated,
            shards_uploaded=shards_uploaded,
            shards_skipped=shards_skipped,
            errors=errors,
        )

    def _upload_shards(
        self,
        uploads: list[UploadItem],
        skip_existing: bool,
    ) -> list[UploadResult]:
        """Upload shards in parallel.

        Args:
            uploads: Upload items
            skip_existing: Skip if exists with same size

        Returns:
            List of upload results
        """
        results = []

        with ThreadPoolExecutor(max_workers=self._concurrency) as executor:
            futures = {
                executor.submit(
                    self._upload_single,
                    upload,
                    skip_existing,
                ): upload
                for upload in uploads
            }

            for future in as_completed(futures):
                upload = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(UploadResult(
                        uri=upload.target_uri,
                        success=False,
                        error=str(e),
                    ))

        return results

    def _upload_single(
        self,
        upload: UploadItem,
        skip_existing: bool,
    ) -> UploadResult:
        """Upload a single item.

        Args:
            upload: Upload item
            skip_existing: Skip if exists with same size

        Returns:
            Upload result
        """
        # Check if exists
        if skip_existing:
            try:
                meta = self._storage.head_object(upload.target_uri)
                if meta is not None:
                    remote_size = meta.get("size", -1)
                    if remote_size == upload.size_bytes:
                        logger.debug(f"Skipping existing: {upload.target_uri}")
                        return UploadResult(
                            uri=upload.target_uri,
                            success=True,
                            skipped=True,
                        )
            except Exception:
                pass  # If head fails, proceed with upload

        # Upload
        try:
            self._storage.put_file(upload.target_uri, upload.source_path)
            logger.debug(f"Uploaded: {upload.target_uri}")
            return UploadResult(
                uri=upload.target_uri,
                success=True,
                skipped=False,
            )
        except Exception as e:
            return UploadResult(
                uri=upload.target_uri,
                success=False,
                error=str(e),
            )
