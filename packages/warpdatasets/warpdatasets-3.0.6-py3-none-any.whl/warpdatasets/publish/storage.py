"""Storage backends for publishing.

Provides put/head/get operations for data uploads.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


class S3Storage:
    """S3 storage backend for publishing.

    Implements the StorageBackend protocol for uploading to S3.
    """

    def __init__(
        self,
        region: str | None = None,
        endpoint_url: str | None = None,
    ):
        """Initialize S3 storage.

        Args:
            region: AWS region
            endpoint_url: Custom endpoint (for MinIO, etc.)
        """
        self._region = region
        self._endpoint_url = endpoint_url
        self._client = None

    @property
    def client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
            except ImportError as e:
                raise ImportError(
                    "boto3 is required for S3 publishing. "
                    "Install it with: pip install boto3"
                ) from e

            kwargs = {}
            if self._region:
                kwargs["region_name"] = self._region
            if self._endpoint_url:
                kwargs["endpoint_url"] = self._endpoint_url

            self._client = boto3.client("s3", **kwargs)

        return self._client

    def _parse_uri(self, uri: str) -> tuple[str, str]:
        """Parse S3 URI into bucket and key."""
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Expected s3:// URI, got: {uri}")
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return bucket, key

    def put_object(self, uri: str, data: bytes) -> None:
        """Upload bytes to a URI.

        Args:
            uri: S3 URI (s3://bucket/key)
            data: Bytes to upload
        """
        bucket, key = self._parse_uri(uri)
        self.client.put_object(Bucket=bucket, Key=key, Body=data)

    def put_file(self, uri: str, path: Path) -> None:
        """Upload a file to a URI.

        Args:
            uri: S3 URI
            path: Local file path
        """
        bucket, key = self._parse_uri(uri)
        self.client.upload_file(str(path), bucket, key)

    def head_object(self, uri: str) -> dict | None:
        """Get object metadata.

        Args:
            uri: S3 URI

        Returns:
            Dict with 'size' and 'etag', or None if not found
        """
        from botocore.exceptions import ClientError

        bucket, key = self._parse_uri(uri)

        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return {
                "size": response.get("ContentLength", 0),
                "etag": response.get("ETag", "").strip('"'),
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise

    def get_object(self, uri: str) -> bytes | None:
        """Get object content.

        Args:
            uri: S3 URI

        Returns:
            Object content as bytes, or None if not found
        """
        from botocore.exceptions import ClientError

        bucket, key = self._parse_uri(uri)

        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise


class FileStorage:
    """Local filesystem storage backend.

    Useful for testing without S3.
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize file storage.

        Args:
            base_path: Base directory (URIs are relative to this)
        """
        self._base_path = base_path

    def _resolve_path(self, uri: str) -> Path:
        """Resolve URI to local path."""
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            return Path(parsed.path)
        elif parsed.scheme == "s3":
            # Map s3://bucket/key to base_path/bucket/key
            if self._base_path is None:
                raise ValueError("base_path required for s3:// URIs")
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            return self._base_path / bucket / key
        else:
            # Assume relative path
            if self._base_path is None:
                return Path(uri)
            return self._base_path / uri

    def put_object(self, uri: str, data: bytes) -> None:
        """Write bytes to a file."""
        path = self._resolve_path(uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def put_file(self, uri: str, source_path: Path) -> None:
        """Copy file to destination."""
        import shutil
        path = self._resolve_path(uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, path)

    def head_object(self, uri: str) -> dict | None:
        """Get file metadata."""
        path = self._resolve_path(uri)
        if not path.exists():
            return None
        return {
            "size": path.stat().st_size,
            "etag": None,
        }

    def get_object(self, uri: str) -> bytes | None:
        """Read file content."""
        path = self._resolve_path(uri)
        if not path.exists():
            return None
        return path.read_bytes()


def create_storage(base_uri: str, **kwargs) -> S3Storage | FileStorage:
    """Create appropriate storage backend for a base URI.

    Args:
        base_uri: Base URI (s3://... or file://...)
        **kwargs: Additional arguments for the storage backend

    Returns:
        Storage backend instance
    """
    parsed = urlparse(base_uri)

    if parsed.scheme == "s3":
        return S3Storage(
            region=kwargs.get("region"),
            endpoint_url=kwargs.get("endpoint_url"),
        )
    elif parsed.scheme == "file" or not parsed.scheme:
        base_path = Path(parsed.path if parsed.scheme == "file" else base_uri)
        return FileStorage(base_path=base_path)
    else:
        raise ValueError(f"Unsupported storage scheme: {parsed.scheme}")
