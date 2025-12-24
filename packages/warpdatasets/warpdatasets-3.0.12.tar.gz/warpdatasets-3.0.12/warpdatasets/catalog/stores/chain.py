"""Chain manifest store - tries multiple stores in order.

Used to check local first, then fall back to remote.
"""

from __future__ import annotations

from warpdatasets.catalog.store import FetchResult, ManifestStore


class ChainManifestStore(ManifestStore):
    """Manifest store that chains multiple stores.

    Tries stores in order, returning the first successful result.
    Used to implement local-first with remote fallback.
    """

    def __init__(self, stores: list[ManifestStore]):
        """Initialize chain manifest store.

        Args:
            stores: List of stores to try, in order
        """
        if not stores:
            raise ValueError("ChainManifestStore requires at least one store")
        self.stores = stores

    def fetch(
        self,
        path: str,
        if_none_match: str | None = None,
        if_modified_since: str | None = None,
    ) -> FetchResult:
        """Fetch from first store that has the manifest."""
        last_result = None

        for store in self.stores:
            result = store.fetch(
                path,
                if_none_match=if_none_match,
                if_modified_since=if_modified_since,
            )

            # Return on success (200) or not-modified (304)
            if result.status in (200, 304):
                return result

            # Keep track of last result for error reporting
            last_result = result

        # All stores failed, return last result (likely 404)
        return last_result or FetchResult(status=404, content=None, etag=None)

    def exists(self, path: str) -> bool:
        """Check if manifest exists in any store."""
        return any(store.exists(path) for store in self.stores)
