"""Tar shard reader for extracting members from tar archives.

Supports local file:// and remote http:// URIs.
Phase 3 implements correctness-first approach (sequential scan).
Phase 6 will add indexing for performance.
"""

from __future__ import annotations

import io
import tarfile
from contextlib import contextmanager
from typing import BinaryIO, Iterator, Sequence
from urllib.parse import urlparse

from warpdatasets.util.errors import RefNotFoundError


class TarReader:
    """Reader for extracting members from tar shard archives.

    Supports reading members by name from one or more tar shards.
    Phase 3 uses sequential scan to find members (correctness first).
    """

    def __init__(self, uris: Sequence[str]):
        """Initialize reader with shard URIs.

        Args:
            uris: List of tar shard URIs (file:// or http://)
        """
        self._uris = list(uris)

    def read_member(self, member_name: str, max_bytes: int | None = None) -> bytes:
        """Read a member's content by name.

        Args:
            member_name: Name of the member to read
            max_bytes: Maximum bytes to read (None for all)

        Returns:
            Member content as bytes.

        Raises:
            RefNotFoundError: If member is not found in any shard.
        """
        for i, uri in enumerate(self._uris):
            result = self._read_member_from_shard(uri, member_name, max_bytes)
            if result is not None:
                return result

        raise RefNotFoundError(
            ref_value=member_name,
            artifact_name="tar_shards",
            shards_searched=len(self._uris),
        )

    @contextmanager
    def open_member(self, member_name: str) -> Iterator[BinaryIO]:
        """Open a member as a binary stream.

        Args:
            member_name: Name of the member to open

        Yields:
            File-like object for reading.

        Raises:
            RefNotFoundError: If member is not found.
        """
        # Read full content and wrap in BytesIO
        # (Phase 3 simplicity - Phase 6 may stream directly)
        content = self.read_member(member_name)
        yield io.BytesIO(content)

    def member_exists(self, member_name: str) -> bool:
        """Check if a member exists in any shard.

        Args:
            member_name: Name of the member to check

        Returns:
            True if member exists, False otherwise.
        """
        for uri in self._uris:
            if self._member_exists_in_shard(uri, member_name):
                return True
        return False

    def _read_member_from_shard(
        self, uri: str, member_name: str, max_bytes: int | None = None
    ) -> bytes | None:
        """Try to read a member from a specific shard.

        Returns None if member not found.
        """
        parsed = urlparse(uri)

        if parsed.scheme == "file" or not parsed.scheme:
            return self._read_member_from_file(
                parsed.path if parsed.scheme == "file" else uri,
                member_name,
                max_bytes,
            )
        elif parsed.scheme in ("http", "https"):
            return self._read_member_from_http(uri, member_name, max_bytes)
        else:
            raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")

    def _read_member_from_file(
        self, path: str, member_name: str, max_bytes: int | None = None
    ) -> bytes | None:
        """Read a member from a local tar file."""
        try:
            with tarfile.open(path, "r") as tar:
                try:
                    member = tar.getmember(member_name)
                except KeyError:
                    return None

                f = tar.extractfile(member)
                if f is None:
                    return None

                if max_bytes is not None:
                    return f.read(max_bytes)
                return f.read()
        except FileNotFoundError:
            return None

    def _read_member_from_http(
        self, url: str, member_name: str, max_bytes: int | None = None
    ) -> bytes | None:
        """Read a member from an HTTP tar file.

        Phase 3: Downloads entire tar to memory for simplicity.
        Phase 6: Will use range requests + index for efficiency.
        """
        import urllib.request

        try:
            with urllib.request.urlopen(url) as response:
                tar_bytes = response.read()
        except Exception:
            return None

        try:
            with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tar:
                try:
                    member = tar.getmember(member_name)
                except KeyError:
                    return None

                f = tar.extractfile(member)
                if f is None:
                    return None

                if max_bytes is not None:
                    return f.read(max_bytes)
                return f.read()
        except Exception:
            return None

    def _member_exists_in_shard(self, uri: str, member_name: str) -> bool:
        """Check if a member exists in a specific shard."""
        parsed = urlparse(uri)

        if parsed.scheme == "file" or not parsed.scheme:
            path = parsed.path if parsed.scheme == "file" else uri
            try:
                with tarfile.open(path, "r") as tar:
                    try:
                        tar.getmember(member_name)
                        return True
                    except KeyError:
                        return False
            except FileNotFoundError:
                return False
        elif parsed.scheme in ("http", "https"):
            # For HTTP, we'd need to download - expensive
            # Just try reading and catch
            return self._read_member_from_http(uri, member_name) is not None
        else:
            return False
