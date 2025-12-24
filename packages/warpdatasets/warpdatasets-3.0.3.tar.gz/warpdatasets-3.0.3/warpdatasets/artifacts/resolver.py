"""Artifact resolver for resolving refs to bytes/streams.

Integrates with manifest artifacts, tar readers, and artifact indices.
Supports local:// URIs for frictionless local development.
Supports portable key-based manifests with location resolution.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Dict, Optional

from warpdatasets.artifacts.tar.reader import TarReader
from warpdatasets.util.errors import RefNotFoundError
from warpdatasets.util.uris import join_base_and_key, local_path_from_uri, file_uri_from_path

if TYPE_CHECKING:
    from warpdatasets.artifacts.index import ArtifactIndex
    from warpdatasets.cache.context import CacheContext
    from warpdatasets.config.settings import Settings
    from warpdatasets.manifest.model import ArtifactDescriptor, Manifest, ShardInfo


class ArtifactResolver:
    """Resolves artifact references to bytes/streams.

    Supports tar_shards artifact kind with optional index for fast lookups.

    When an artifact has an index:
    - Uses O(1) lookup to find member location
    - Reads directly from shard using offset info

    When no index:
    - Falls back to TarReader scanning (Phase 3 behavior)
    """

    def __init__(
        self,
        manifest: Optional["Manifest"] = None,
        cache_context: Optional["CacheContext"] = None,
        artifacts: Optional[Dict[str, "ArtifactDescriptor"]] = None,
        settings: Optional["Settings"] = None,
    ):
        """Initialize resolver.

        Args:
            manifest: Manifest containing artifact definitions
            cache_context: Optional cache context for caching shards
            artifacts: Alternative to manifest - direct artifacts dict
            settings: Optional settings for resolving local:// URIs

        Note:
            Either manifest or artifacts must be provided.
        """
        self._manifest = manifest
        if manifest is not None:
            self._artifacts = manifest.artifacts
        elif artifacts is not None:
            self._artifacts = artifacts
        else:
            raise ValueError("Either manifest or artifacts must be provided")

        self._cache_context = cache_context
        self._settings = settings
        self._reader_cache: Dict[str, TarReader] = {}
        self._index_cache: Dict[str, "ArtifactIndex"] = {}

    def open(self, artifact_name: str, ref_value: str) -> BinaryIO:
        """Open a member as a binary stream.

        Args:
            artifact_name: Name of the artifact
            ref_value: Reference value (e.g., tar member path)

        Returns:
            File-like object for reading (BytesIO).

        Raises:
            KeyError: If artifact doesn't exist.
            RefNotFoundError: If ref is not found.
        """
        content = self.read_bytes(artifact_name, ref_value)
        return io.BytesIO(content)

    def read_bytes(
        self, artifact_name: str, ref_value: str, max_bytes: Optional[int] = None
    ) -> bytes:
        """Read member bytes.

        Supports:
        - tar_shards: Uses index for direct reads when available, falls back to scanning
        - directory: Reads directly from local directory

        Args:
            artifact_name: Name of the artifact
            ref_value: Reference value (e.g., tar member path or file path)
            max_bytes: Maximum bytes to read (None for all)

        Returns:
            Member content as bytes.

        Raises:
            KeyError: If artifact doesn't exist.
            RefNotFoundError: If ref is not found.
        """
        artifact = self._get_artifact(artifact_name)

        # Handle directory artifacts
        if artifact.kind == "directory":
            return self._read_from_directory(artifact_name, artifact, ref_value, max_bytes)

        # Handle tar_shards artifacts
        # Try index-based lookup first
        if artifact.index is not None:
            index = self._get_index(artifact_name)
            if index is not None:
                entry = index.lookup(ref_value)
                if entry is not None:
                    # Direct read using offset
                    return self._read_direct(
                        artifact_name, artifact, entry, max_bytes
                    )
                # Entry not in index - fall through to scanning

        # Fall back to TarReader scanning
        reader = self._get_reader(artifact_name)
        return reader.read_member(ref_value, max_bytes=max_bytes)

    def _read_from_directory(
        self,
        artifact_name: str,
        artifact: "ArtifactDescriptor",
        ref_value: str,
        max_bytes: Optional[int] = None,
    ) -> bytes:
        """Read file from a directory artifact.

        Args:
            artifact_name: Name of the artifact
            artifact: Directory artifact descriptor
            ref_value: Relative file path within the directory
            max_bytes: Maximum bytes to read (None for all)

        Returns:
            File content as bytes.

        Raises:
            RefNotFoundError: If file doesn't exist.
        """
        # Directory artifact should have exactly one "shard" pointing to the directory
        if not artifact.shards:
            raise ValueError("Directory artifact has no directory path")

        base_uri = artifact.shards[0].uri
        base_path = Path(self._resolve_uri(base_uri))

        # Resolve ref_value relative to base directory
        file_path = base_path / ref_value

        # Security check: ensure path doesn't escape the base directory
        try:
            file_path = file_path.resolve()
            base_path = base_path.resolve()
            if not str(file_path).startswith(str(base_path)):
                raise RefNotFoundError(ref_value, artifact_name)
        except (OSError, ValueError) as e:
            raise RefNotFoundError(ref_value, artifact_name) from e

        if not file_path.exists():
            raise RefNotFoundError(ref_value, artifact_name)

        try:
            if max_bytes is not None:
                with open(file_path, "rb") as f:
                    return f.read(max_bytes)
            else:
                return file_path.read_bytes()
        except Exception as e:
            raise RefNotFoundError(ref_value, artifact_name) from e

    def _get_artifact(self, artifact_name: str) -> "ArtifactDescriptor":
        """Get artifact descriptor by name."""
        if artifact_name not in self._artifacts:
            raise KeyError(f"Artifact '{artifact_name}' not found")
        return self._artifacts[artifact_name]

    def _data_locations(self) -> list[str]:
        """Get ordered list of data locations to try when resolving shard keys.

        Priority order:
        1. Local mirror (if settings available and in appropriate mode)
        2. Manifest locations
        3. Derived remote location from settings.manifest_base

        Returns:
            List of base URIs to try, in priority order
        """
        if self._manifest is None:
            return []

        ws, name = self._manifest.dataset.split("/", 1)
        version = self._manifest.version_hash

        locs: list[str] = []

        # Local mirror - try first if settings available
        if self._settings is not None and self._settings.mode in ("local", "hybrid", "auto"):
            local_base = f"local://data/{ws}/{name}/{version}/"
            locs.append(local_base)

        # Manifest-specified locations
        if self._manifest.locations:
            locs.extend(self._manifest.locations)

        # Derived remote location from manifest_base
        if self._settings is not None and self._settings.manifest_base:
            derived = f"{self._settings.manifest_base.rstrip('/')}/data/{ws}/{name}/{version}/"
            if derived not in locs:
                locs.append(derived)

        # De-duplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for loc in locs:
            if loc and loc not in seen:
                seen.add(loc)
                result.append(loc)

        return result

    def _resolve_shard_uri(self, shard: "ShardInfo") -> str:
        """Resolve a shard to a usable URI.

        For legacy shards with uri, returns the uri directly.
        For portable shards with key, tries locations in priority order.

        Args:
            shard: ShardInfo with either uri or key

        Returns:
            Resolved URI (file://, s3://, etc.)
        """
        # Legacy: if shard has uri, use it directly
        if shard.uri is not None:
            return shard.uri

        # Portable: resolve key against locations
        key = shard.key
        if key is None:
            raise ValueError("Shard has neither uri nor key")

        workspace_root = self._settings.workspace_root if self._settings else Path.home() / ".warpdatasets"

        # Try each location in priority order
        for base in self._data_locations():
            candidate = join_base_and_key(base, key)

            # Check if it's a local-ish URI and if the file exists
            local_path = local_path_from_uri(candidate, workspace_root)
            if local_path is not None:
                if local_path.exists():
                    return file_uri_from_path(local_path)
                # Local path doesn't exist, try next location
                continue

            # Remote candidate - apply cache context if available
            if self._cache_context is not None:
                candidate = self._cache_context.resolve_uri(candidate)

            # Return first remote candidate (assume it exists)
            return candidate

        raise FileNotFoundError(f"No valid location found for shard key={key}")

    def _get_index(self, artifact_name: str) -> Optional["ArtifactIndex"]:
        """Get or load index for an artifact.

        Returns None if index not available or fails to load.
        """
        if artifact_name in self._index_cache:
            return self._index_cache[artifact_name]

        artifact = self._get_artifact(artifact_name)
        if artifact.index is None:
            return None

        try:
            # Resolve index URI - handle both legacy uri and portable key
            index_info = artifact.index
            if index_info.uri is not None:
                index_uri = index_info.uri
            elif index_info.key is not None:
                # Resolve key against locations
                from warpdatasets.manifest.model import ShardInfo
                temp_shard = ShardInfo(key=index_info.key)
                index_uri = self._resolve_shard_uri(temp_shard)
            else:
                return None

            index = self._load_index(index_uri)
            self._index_cache[artifact_name] = index
            return index
        except Exception:
            # If index loading fails, return None to allow fallback
            return None

    def _resolve_uri(self, uri: str) -> str:
        """Resolve a URI to a form suitable for I/O operations.

        Handles:
        - local:// URIs -> resolved via settings.workspace_root
        - file:// URIs -> stripped to local path
        - Relative paths -> resolved via settings.workspace_root
        - Other URIs -> returned as-is

        Args:
            uri: URI to resolve

        Returns:
            Resolved URI (may be a local path string or original URI)
        """
        # Handle local:// scheme
        if uri.startswith("local://"):
            if self._settings is not None:
                resolved = self._settings.resolve_local_uri(uri)
                return str(resolved)
            # Fallback: strip scheme and treat as relative
            return uri[8:]

        # Handle file:// scheme (strip scheme prefix)
        if uri.startswith("file://"):
            return uri[7:]

        # Handle relative paths (no scheme)
        if "://" not in uri and not uri.startswith("/"):
            if self._settings is not None:
                resolved = self._settings.resolve_local_uri(uri)
                return str(resolved)
            # Return as-is if no settings
            return uri

        # Return other URIs unchanged
        return uri

    def _load_index(self, uri: str) -> "ArtifactIndex":
        """Load index from URI."""
        from warpdatasets.artifacts.index import ArtifactIndex

        # Resolve local:// and relative URIs first
        resolved_uri = self._resolve_uri(uri)

        # Then apply cache context if available
        if self._cache_context is not None:
            resolved_uri = self._cache_context.resolve_uri(resolved_uri)

        # Load based on URI scheme
        if resolved_uri.startswith("/"):
            # Local absolute path
            return ArtifactIndex.from_parquet(Path(resolved_uri))
        elif resolved_uri.startswith("file://"):
            path = Path(resolved_uri[7:])
            return ArtifactIndex.from_parquet(path)
        elif resolved_uri.startswith("http://") or resolved_uri.startswith("https://"):
            # Remote HTTP - fetch bytes
            data = self._fetch_uri(resolved_uri)
            return ArtifactIndex.from_bytes(data)
        elif resolved_uri.startswith("s3://"):
            # Remote S3 - fetch bytes
            data = self._fetch_uri(resolved_uri)
            return ArtifactIndex.from_bytes(data)
        else:
            # Unknown scheme or relative path - try as local path
            return ArtifactIndex.from_parquet(Path(resolved_uri))

    def _fetch_uri(self, uri: str) -> bytes:
        """Fetch bytes from a URI."""
        if uri.startswith("http://") or uri.startswith("https://"):
            import urllib.request
            with urllib.request.urlopen(uri) as resp:
                return resp.read()
        elif uri.startswith("s3://"):
            import boto3
            parts = uri[5:].split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            s3 = boto3.client("s3")
            resp = s3.get_object(Bucket=bucket, Key=key)
            return resp["Body"].read()
        else:
            raise ValueError(f"Unsupported URI scheme: {uri}")

    def _read_direct(
        self,
        artifact_name: str,
        artifact: "ArtifactDescriptor",
        entry: "IndexEntry",
        max_bytes: Optional[int] = None,
    ) -> bytes:
        """Read member directly using index offset info.

        Args:
            artifact_name: Name of the artifact
            artifact: Artifact descriptor
            entry: Index entry with shard/offset info
            max_bytes: Maximum bytes to read

        Returns:
            Member content as bytes.
        """
        from warpdatasets.artifacts.index import IndexEntry

        # Get shard and resolve its URI
        shard = artifact.shards[entry.shard_idx]
        shard_uri = self._resolve_shard_uri(shard)

        # Read from shard
        size = entry.payload_size
        if max_bytes is not None:
            size = min(size, max_bytes)

        return self._read_from_shard(shard_uri, entry.payload_offset, size)

    def _read_from_shard(self, uri: str, offset: int, size: int) -> bytes:
        """Read bytes from a shard at offset.

        Args:
            uri: Shard URI (may be resolved to local path)
            offset: Byte offset to start reading
            size: Number of bytes to read

        Returns:
            Bytes read from shard.
        """
        # Resolve local:// and relative URIs first
        resolved_uri = self._resolve_uri(uri)

        # Local file read
        if resolved_uri.startswith("/"):
            with open(resolved_uri, "rb") as f:
                f.seek(offset)
                return f.read(size)
        elif resolved_uri.startswith("file://"):
            path = resolved_uri[7:]
            with open(path, "rb") as f:
                f.seek(offset)
                return f.read(size)
        elif resolved_uri.startswith("http://") or resolved_uri.startswith("https://"):
            # HTTP range read
            return self._http_range_read(resolved_uri, offset, size)
        elif resolved_uri.startswith("s3://"):
            # S3 range read
            return self._s3_range_read(resolved_uri, offset, size)
        else:
            # Unknown scheme - try as local path
            with open(resolved_uri, "rb") as f:
                f.seek(offset)
                return f.read(size)

    def _http_range_read(self, url: str, offset: int, size: int) -> bytes:
        """Perform HTTP range read."""
        import urllib.request

        end = offset + size - 1
        req = urllib.request.Request(url)
        req.add_header("Range", f"bytes={offset}-{end}")

        with urllib.request.urlopen(req) as resp:
            return resp.read()

    def _s3_range_read(self, uri: str, offset: int, size: int) -> bytes:
        """Perform S3 range read."""
        import boto3

        parts = uri[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""

        end = offset + size - 1
        s3 = boto3.client("s3")
        resp = s3.get_object(
            Bucket=bucket,
            Key=key,
            Range=f"bytes={offset}-{end}",
        )
        return resp["Body"].read()

    def _get_reader(self, artifact_name: str) -> TarReader:
        """Get or create a TarReader for an artifact (fallback path).

        Args:
            artifact_name: Name of the artifact

        Returns:
            TarReader for the artifact.
        """
        if artifact_name in self._reader_cache:
            return self._reader_cache[artifact_name]

        artifact = self._get_artifact(artifact_name)

        if artifact.kind != "tar_shards":
            raise ValueError(
                f"Unsupported artifact kind '{artifact.kind}'. "
                "Only 'tar_shards' is supported."
            )

        # Resolve each shard URI (handles both legacy uri and portable key)
        uris = [self._resolve_shard_uri(s) for s in artifact.shards]

        # Resolve local:// URIs to absolute paths
        resolved_uris = [self._resolve_uri(uri) for uri in uris]

        reader = TarReader(resolved_uris)
        self._reader_cache[artifact_name] = reader
        return reader
