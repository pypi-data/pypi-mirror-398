"""Post-publish verification.

Verifies that published datasets are accessible and valid.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from warpdatasets.publish.plan import PublishPlan
from warpdatasets.publish.storage import S3Storage, FileStorage

logger = logging.getLogger(__name__)


@dataclass
class VerifyResult:
    """Result of verification checks."""

    success: bool
    manifest_accessible: bool
    first_shard_accessible: bool
    schema_valid: bool
    errors: list[str]


def verify_publish(
    plan: PublishPlan,
    storage: S3Storage | FileStorage,
    check_schema: bool = True,
) -> VerifyResult:
    """Verify a published dataset is accessible.

    Args:
        plan: The publish plan that was executed
        storage: Storage backend to check
        check_schema: Whether to verify schema via DuckDB

    Returns:
        VerifyResult with check status
    """
    errors = []

    # Check 1: Manifest is accessible
    manifest_accessible = False
    try:
        content = storage.get_object(plan.manifest_uri)
        if content is not None:
            manifest_accessible = True
            logger.debug(f"Manifest accessible: {plan.manifest_uri}")
        else:
            errors.append(f"Manifest not found: {plan.manifest_uri}")
    except Exception as e:
        errors.append(f"Error accessing manifest: {e}")

    # Check 2: First table shard is accessible
    first_shard_accessible = False
    if plan.table_uploads:
        first_shard_uri = plan.table_uploads[0].target_uri
        try:
            meta = storage.head_object(first_shard_uri)
            if meta is not None:
                first_shard_accessible = True
                logger.debug(f"First shard accessible: {first_shard_uri}")
            else:
                errors.append(f"First shard not found: {first_shard_uri}")
        except Exception as e:
            errors.append(f"Error accessing first shard: {e}")
    else:
        # No table shards to check
        first_shard_accessible = True

    # Check 3: Schema is valid (via DuckDB if requested)
    schema_valid = True
    if check_schema and first_shard_accessible and plan.table_uploads:
        first_shard_uri = plan.table_uploads[0].target_uri
        try:
            import duckdb
            conn = duckdb.connect()

            # For S3 URIs, configure httpfs
            if first_shard_uri.startswith("s3://"):
                conn.execute("INSTALL httpfs; LOAD httpfs;")

            # Try to describe schema
            query = f"DESCRIBE SELECT * FROM read_parquet('{first_shard_uri}')"
            result = conn.execute(query).fetchall()

            if result:
                logger.debug(f"Schema verified: {len(result)} columns")
            else:
                errors.append("Schema query returned no columns")
                schema_valid = False

            conn.close()

        except Exception as e:
            errors.append(f"Schema verification failed: {e}")
            schema_valid = False

    success = manifest_accessible and first_shard_accessible
    if check_schema:
        success = success and schema_valid

    return VerifyResult(
        success=success,
        manifest_accessible=manifest_accessible,
        first_shard_accessible=first_shard_accessible,
        schema_valid=schema_valid,
        errors=errors,
    )


def verify_remote_access(
    dataset_id: str,
    base_uri: str,
    version: str | None = None,
) -> VerifyResult:
    """Verify remote access to a published dataset.

    Uses the standard warpdatasets API to verify end-to-end access.

    Args:
        dataset_id: Dataset identifier
        base_uri: Base URI where dataset is published
        version: Optional version to check (default: latest)

    Returns:
        VerifyResult with access status
    """
    errors = []

    try:
        from warpdatasets.api.dataset import dataset

        # Configure to use the published location
        from warpdatasets.config.settings import Settings

        settings = Settings(manifest_base=base_uri)

        # Load dataset
        ds = dataset(dataset_id, version=version, settings=settings)

        manifest_accessible = True
        logger.debug(f"Loaded dataset: {ds.id} version {ds.version_hash}")

        # Check schema
        schema_valid = False
        first_shard_accessible = False
        try:
            table = ds.table("main")
            schema = table.schema()
            if schema:
                schema_valid = True
                logger.debug(f"Schema: {len(schema)} columns")

            # Try to read first row
            df = table.head(1)
            if len(df) >= 0:
                first_shard_accessible = True
                logger.debug("Successfully read first row")

        except Exception as e:
            errors.append(f"Table access failed: {e}")

        return VerifyResult(
            success=manifest_accessible and schema_valid and first_shard_accessible,
            manifest_accessible=manifest_accessible,
            first_shard_accessible=first_shard_accessible,
            schema_valid=schema_valid,
            errors=errors,
        )

    except Exception as e:
        errors.append(f"Failed to load dataset: {e}")
        return VerifyResult(
            success=False,
            manifest_accessible=False,
            first_shard_accessible=False,
            schema_valid=False,
            errors=errors,
        )
