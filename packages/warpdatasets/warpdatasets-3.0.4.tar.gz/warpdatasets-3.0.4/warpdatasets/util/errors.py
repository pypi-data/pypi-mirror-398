"""Typed exceptions with user-facing messages.

All exceptions include:
- A short message describing the problem
- Remediation hints for how to fix it
"""

from __future__ import annotations


class WarpDatasetsError(Exception):
    """Base exception for all warpdatasets errors."""

    def __init__(self, message: str, remediation: str | None = None):
        self.message = message
        self.remediation = remediation
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.remediation:
            return f"{self.message}\n\nHow to fix: {self.remediation}"
        return self.message


class DatasetNotFoundError(WarpDatasetsError):
    """Dataset does not exist or is not accessible."""

    def __init__(self, dataset_id: str, details: str | None = None):
        message = f"Dataset '{dataset_id}' not found."
        if details:
            message = f"{message} {details}"
        super().__init__(
            message=message,
            remediation=(
                "Check that the dataset ID is correct (format: workspace/name). "
                "Verify the dataset has been published and you have access permissions."
            ),
        )
        self.dataset_id = dataset_id


class ManifestNotFoundError(WarpDatasetsError):
    """Manifest version does not exist."""

    def __init__(self, dataset_id: str, version: str):
        super().__init__(
            message=f"Manifest version '{version}' not found for dataset '{dataset_id}'.",
            remediation=(
                "Check that the version hash is correct. "
                "Use version='latest' or omit version to get the latest published version."
            ),
        )
        self.dataset_id = dataset_id
        self.version = version


class ManifestInvalidError(WarpDatasetsError):
    """Manifest content is invalid or corrupted."""

    def __init__(self, dataset_id: str, details: str):
        super().__init__(
            message=f"Invalid manifest for dataset '{dataset_id}': {details}",
            remediation=(
                "The manifest may be corrupted. Try clearing the cache with "
                "'warpdata cache gc' and retry. If the problem persists, "
                "contact the dataset publisher."
            ),
        )
        self.dataset_id = dataset_id


class EngineNotReadyError(WarpDatasetsError):
    """DuckDB engine is not properly configured."""

    def __init__(self, details: str):
        super().__init__(
            message=f"Query engine not ready: {details}",
            remediation=(
                "Ensure DuckDB is installed with remote access extensions. "
                "For S3 access, configure AWS credentials via environment variables "
                "(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or AWS profile. "
                "Run 'warpdata doctor' to diagnose configuration issues."
            ),
        )


class LargeDataError(WarpDatasetsError):
    """Operation would load too much data into memory."""

    def __init__(self, row_count: int | None, threshold: int):
        if row_count is not None:
            message = (
                f"Dataset has {row_count:,} rows, which exceeds the safety threshold "
                f"of {threshold:,} rows for loading into memory."
            )
        else:
            message = (
                f"Dataset size is unknown but appears large. "
                f"Safety threshold is {threshold:,} rows."
            )
        super().__init__(
            message=message,
            remediation=(
                "Options:\n"
                "  1. Use .to_pandas(limit=N) to load only N rows\n"
                "  2. Use .to_pandas(allow_large=True) to bypass this check\n"
                "  3. Use .duckdb() for lazy evaluation and streaming\n"
                "  4. Use .batches() for memory-efficient iteration"
            ),
        )
        self.row_count = row_count
        self.threshold = threshold


class AuthenticationError(WarpDatasetsError):
    """Authentication/credentials issue."""

    def __init__(self, details: str):
        super().__init__(
            message=f"Authentication failed: {details}",
            remediation=(
                "For AWS/S3:\n"
                "  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars, or\n"
                "  - Set AWS_PROFILE to use a named profile, or\n"
                "  - Configure credentials in ~/.aws/credentials\n"
                "Run 'warpdata doctor' to verify your configuration."
            ),
        )


class PermissionError(WarpDatasetsError):
    """Permission denied accessing a resource."""

    def __init__(self, resource: str, details: str | None = None):
        message = f"Permission denied accessing '{resource}'."
        if details:
            message = f"{message} {details}"
        super().__init__(
            message=message,
            remediation=(
                "Check that your credentials have the required permissions. "
                "For S3, ensure your IAM role/user has s3:GetObject permission "
                "on the bucket and prefix. Contact the dataset owner if you "
                "need access granted."
            ),
        )
        self.resource = resource


class RefNotFoundError(WarpDatasetsError):
    """Reference to raw data member not found in artifact shards."""

    def __init__(self, ref_value: str, artifact_name: str, shards_searched: int = 0):
        message = f"Reference '{ref_value}' not found in artifact '{artifact_name}'."
        if shards_searched > 0:
            message = f"{message} Searched {shards_searched} shard(s)."
        super().__init__(
            message=message,
            remediation=(
                "Verify that the reference value in your data matches a member "
                "in the artifact tar shards. The binding may be incorrect, or "
                "the raw data archive may be incomplete."
            ),
        )
        self.ref_value = ref_value
        self.artifact_name = artifact_name
        self.shards_searched = shards_searched
