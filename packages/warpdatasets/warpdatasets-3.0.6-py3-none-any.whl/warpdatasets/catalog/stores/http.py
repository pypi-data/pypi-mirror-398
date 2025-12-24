"""HTTP manifest store backend."""

from __future__ import annotations

import urllib.request
import urllib.error
from urllib.parse import urljoin

from warpdatasets.catalog.store import FetchResult, ManifestStore


class HttpManifestStore(ManifestStore):
    """Manifest store backed by HTTP/HTTPS server."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize HTTP manifest store.

        Args:
            base_url: Base URL for manifests (e.g., "https://example.com/warp/manifests/")
            timeout: Request timeout in seconds
        """
        # Ensure base URL ends with /
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

    def fetch(
        self,
        path: str,
        if_none_match: str | None = None,
        if_modified_since: str | None = None,
    ) -> FetchResult:
        """Fetch a manifest via HTTP."""
        url = urljoin(self.base_url, path)

        # Build request with conditional headers
        request = urllib.request.Request(url)

        if if_none_match:
            request.add_header("If-None-Match", if_none_match)
        if if_modified_since:
            request.add_header("If-Modified-Since", if_modified_since)

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content = response.read()
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")

                return FetchResult(
                    status=200,
                    content=content,
                    etag=etag,
                    last_modified=last_modified,
                )

        except urllib.error.HTTPError as e:
            if e.code == 304:
                return FetchResult(
                    status=304,
                    content=None,
                    etag=e.headers.get("ETag") if e.headers else None,
                )
            elif e.code == 404:
                return FetchResult(
                    status=404,
                    content=None,
                    etag=None,
                )
            else:
                # Re-raise for other errors
                return FetchResult(
                    status=e.code,
                    content=None,
                    etag=None,
                )

        except urllib.error.URLError:
            # Network error
            return FetchResult(
                status=0,
                content=None,
                etag=None,
            )

    def exists(self, path: str) -> bool:
        """Check if manifest exists via HEAD request."""
        url = urljoin(self.base_url, path)
        request = urllib.request.Request(url, method="HEAD")

        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                return True
        except urllib.error.HTTPError as e:
            return e.code != 404
        except urllib.error.URLError:
            return False
