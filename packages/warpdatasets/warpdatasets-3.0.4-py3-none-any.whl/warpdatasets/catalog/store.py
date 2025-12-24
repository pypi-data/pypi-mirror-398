"""Manifest store interface and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FetchResult:
    """Result of a manifest fetch operation."""

    status: int  # HTTP status code (200, 304, 404, etc.)
    content: bytes | None  # Content if status is 200
    etag: str | None  # ETag header value
    last_modified: str | None = None  # Last-Modified header value

    @property
    def is_success(self) -> bool:
        """Check if fetch was successful."""
        return self.status == 200

    @property
    def is_not_modified(self) -> bool:
        """Check if content hasn't changed (304 response)."""
        return self.status == 304

    @property
    def is_not_found(self) -> bool:
        """Check if resource doesn't exist."""
        return self.status == 404


class ManifestStore(ABC):
    """Abstract base class for manifest storage backends."""

    @abstractmethod
    def fetch(
        self,
        path: str,
        if_none_match: str | None = None,
        if_modified_since: str | None = None,
    ) -> FetchResult:
        """Fetch a manifest from the store.

        Args:
            path: Path to the manifest (e.g., "workspace/name/latest.json")
            if_none_match: ETag for conditional request (returns 304 if match)
            if_modified_since: Last-Modified for conditional request

        Returns:
            FetchResult with status, content (if 200), and caching headers
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a manifest exists."""
        pass
