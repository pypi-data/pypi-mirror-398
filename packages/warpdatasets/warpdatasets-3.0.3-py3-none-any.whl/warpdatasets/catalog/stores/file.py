"""File-based manifest store for local development.

Supports local-first workflows where manifests are stored in the workspace.
"""

from __future__ import annotations

import os
from pathlib import Path

from warpdatasets.catalog.store import FetchResult, ManifestStore


def _file_manifests_allowed() -> bool:
    """Check if file manifests are allowed.

    Returns True when:
    - WARPDATASETS_ALLOW_FILE_MANIFESTS=1 (legacy)
    - WARPDATASETS_SCOPE=local (default for local-first)
    - WARPDATASETS_MODE is auto/local with no manifest_base
    """
    # Legacy explicit flag
    if os.environ.get("WARPDATASETS_ALLOW_FILE_MANIFESTS", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True

    # Local scope (default is "local")
    scope = os.environ.get("WARPDATASETS_SCOPE", "local")
    if scope == "local":
        return True

    return False


class FileManifestStore(ManifestStore):
    """Manifest store backed by local filesystem.

    Used for local-first workflows where datasets are registered
    in the local workspace before publishing.
    """

    def __init__(self, base_path: Path | str, *, skip_check: bool = False):
        """Initialize file manifest store.

        Args:
            base_path: Base directory for manifests
            skip_check: Skip file manifest permission check (for internal use)

        Raises:
            RuntimeError: If file manifests are not allowed
        """
        if not skip_check and not _file_manifests_allowed():
            raise RuntimeError(
                "File manifest store is disabled. "
                "Set WARPDATASETS_SCOPE=local for local development."
            )

        self.base_path = Path(base_path)

    def _make_path(self, path: str) -> Path:
        """Build filesystem path."""
        return self.base_path / path

    def fetch(
        self,
        path: str,
        if_none_match: str | None = None,
        if_modified_since: str | None = None,
    ) -> FetchResult:
        """Fetch a manifest from filesystem."""
        file_path = self._make_path(path)

        if not file_path.exists():
            return FetchResult(
                status=404,
                content=None,
                etag=None,
            )

        try:
            content = file_path.read_bytes()

            # Generate ETag from content hash
            import hashlib

            etag = hashlib.md5(content).hexdigest()

            # Check if-none-match
            if if_none_match and if_none_match == etag:
                return FetchResult(
                    status=304,
                    content=None,
                    etag=etag,
                )

            # Get modification time
            stat = file_path.stat()
            from datetime import datetime, timezone

            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            last_modified = mtime.strftime("%a, %d %b %Y %H:%M:%S GMT")

            return FetchResult(
                status=200,
                content=content,
                etag=etag,
                last_modified=last_modified,
            )

        except IOError:
            return FetchResult(
                status=500,
                content=None,
                etag=None,
            )

    def exists(self, path: str) -> bool:
        """Check if manifest exists on filesystem."""
        return self._make_path(path).exists()
