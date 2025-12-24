"""URI utilities for portable manifest handling.

Provides helpers to:
- Join base URIs with relative keys safely
- Test for local-ish URIs
- Convert between URI forms
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


def join_base_and_key(base: str, key: str) -> str:
    """Join a base URI with a relative key.

    Args:
        base: Base URI (e.g., "s3://bucket/path/" or "local://data/ws/name/version/")
        key: Relative key (e.g., "tables/main/shard-00000.parquet")

    Returns:
        Combined URI
    """
    base = base.rstrip("/") + "/"
    key = key.lstrip("/")
    return base + key


def is_localish_uri(uri: str) -> bool:
    """Check if a URI is local-ish (file://, local://, or no scheme).

    Args:
        uri: URI to check

    Returns:
        True if the URI is local-ish
    """
    return uri.startswith(("file://", "local://")) or ("://" not in uri)


def is_remote_uri(uri: str) -> bool:
    """Check if a URI is remote (s3://, http://, https://).

    Args:
        uri: URI to check

    Returns:
        True if the URI is remote
    """
    return uri.startswith(("s3://", "http://", "https://", "gs://"))


def local_path_from_uri(uri: str, workspace_root: Path) -> Path | None:
    """Convert a local-ish URI to an absolute Path.

    Args:
        uri: URI (local://, file://, or relative path)
        workspace_root: Workspace root for resolving local:// and relative paths

    Returns:
        Absolute Path if URI is local-ish, None otherwise
    """
    if uri.startswith("local://"):
        return workspace_root / uri[8:]
    if uri.startswith("file://"):
        return Path(uri[7:])
    if "://" not in uri:
        # Relative path
        return workspace_root / uri
    return None


def file_uri_from_path(p: Path) -> str:
    """Convert a Path to a file:// URI.

    Args:
        p: Path to convert

    Returns:
        file:// URI
    """
    return p.resolve().as_uri()


def parse_uri_scheme(uri: str) -> str:
    """Parse the scheme from a URI.

    Args:
        uri: URI to parse

    Returns:
        Scheme (e.g., "s3", "local", "file") or empty string if no scheme
    """
    parsed = urlparse(uri)
    return parsed.scheme.lower()


def normalize_local_uri(uri: str, workspace_root: Path) -> str:
    """Normalize a local URI to file:// form if it exists locally.

    This is used for resolution - tries to find the local path and
    returns a file:// URI if it exists, otherwise returns the original.

    Args:
        uri: URI to normalize
        workspace_root: Workspace root for resolving local:// paths

    Returns:
        Normalized URI (file:// if local exists, original otherwise)
    """
    local_path = local_path_from_uri(uri, workspace_root)
    if local_path is not None and local_path.exists():
        return file_uri_from_path(local_path)
    return uri
