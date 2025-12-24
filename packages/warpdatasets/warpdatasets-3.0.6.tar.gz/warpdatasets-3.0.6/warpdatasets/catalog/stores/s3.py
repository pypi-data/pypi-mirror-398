"""S3 manifest store backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from warpdatasets.catalog.store import FetchResult, ManifestStore

if TYPE_CHECKING:
    pass


class S3ManifestStore(ManifestStore):
    """Manifest store backed by S3.

    Requires boto3 to be installed.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "warp/manifests",
        region: str | None = None,
        endpoint_url: str | None = None,
    ):
        """Initialize S3 manifest store.

        Args:
            bucket: S3 bucket name
            prefix: Key prefix for manifests
            region: AWS region (optional, uses default if not specified)
            endpoint_url: Custom endpoint URL (for MinIO, LocalStack, etc.)
        """
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        self.endpoint_url = endpoint_url
        self._client = None

    @property
    def client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
            except ImportError as e:
                raise ImportError(
                    "boto3 is required for S3 access. "
                    "Install it with: pip install warpdatasets[s3]"
                ) from e

            kwargs = {}
            if self.region:
                kwargs["region_name"] = self.region
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url

            self._client = boto3.client("s3", **kwargs)

        return self._client

    def _make_key(self, path: str) -> str:
        """Build S3 key from path."""
        return f"{self.prefix}/{path}" if self.prefix else path

    def fetch(
        self,
        path: str,
        if_none_match: str | None = None,
        if_modified_since: str | None = None,
    ) -> FetchResult:
        """Fetch a manifest from S3."""
        from botocore.exceptions import ClientError

        key = self._make_key(path)

        try:
            kwargs = {"Bucket": self.bucket, "Key": key}

            if if_none_match:
                kwargs["IfNoneMatch"] = if_none_match
            if if_modified_since:
                kwargs["IfModifiedSince"] = if_modified_since

            response = self.client.get_object(**kwargs)

            content = response["Body"].read()
            etag = response.get("ETag", "").strip('"')
            last_modified = None
            if "LastModified" in response:
                last_modified = response["LastModified"].strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            return FetchResult(
                status=200,
                content=content,
                etag=etag,
                last_modified=last_modified,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "304" or error_code == "NotModified":
                return FetchResult(
                    status=304,
                    content=None,
                    etag=if_none_match,
                )
            elif error_code in ("404", "NoSuchKey"):
                return FetchResult(
                    status=404,
                    content=None,
                    etag=None,
                )
            elif error_code in ("403", "AccessDenied"):
                return FetchResult(
                    status=403,
                    content=None,
                    etag=None,
                )
            else:
                # Other error
                return FetchResult(
                    status=500,
                    content=None,
                    etag=None,
                )

    def exists(self, path: str) -> bool:
        """Check if manifest exists in S3."""
        from botocore.exceptions import ClientError

        key = self._make_key(path)

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
