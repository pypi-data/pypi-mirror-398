"""FileRef - base class for typed file references.

Provides lazy, remote-first raw data access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class ArtifactResolver(Protocol):
    """Protocol for resolving artifact references to bytes/streams."""

    def open(self, artifact_name: str, ref_value: str) -> BinaryIO:
        """Open a member as a binary stream."""
        ...

    def read_bytes(
        self, artifact_name: str, ref_value: str, max_bytes: int | None = None
    ) -> bytes:
        """Read member bytes."""
        ...


class FileRef:
    """A resolvable reference to a raw file.

    FileRef is lazy - construction does not download bytes.
    Bytes are only fetched when open(), read_bytes(), etc. are called.

    Attributes:
        artifact_name: Name of the artifact in the manifest
        ref_value: The reference value (e.g., member path in tar)
    """

    def __init__(
        self,
        artifact_name: str,
        ref_value: str,
        resolver: ArtifactResolver,
    ):
        """Initialize a file reference.

        Args:
            artifact_name: Name of the artifact
            ref_value: Reference value (e.g., tar member path)
            resolver: Resolver for fetching bytes
        """
        self._artifact_name = artifact_name
        self._ref_value = ref_value
        self._resolver = resolver

    @property
    def artifact_name(self) -> str:
        """Get the artifact name."""
        return self._artifact_name

    @property
    def ref_value(self) -> str:
        """Get the reference value."""
        return self._ref_value

    def open(self) -> BinaryIO:
        """Open the file as a binary stream.

        Returns:
            A file-like object for reading bytes.
        """
        return self._resolver.open(self._artifact_name, self._ref_value)

    def read_bytes(self, max_bytes: int | None = None) -> bytes:
        """Read the file bytes.

        Args:
            max_bytes: Maximum bytes to read (None for all).

        Returns:
            File contents as bytes.
        """
        return self._resolver.read_bytes(
            self._artifact_name, self._ref_value, max_bytes=max_bytes
        )

    def info(self) -> dict:
        """Get reference information without fetching bytes.

        Returns:
            Dict with artifact, ref, and other metadata.
        """
        return {
            "artifact": self._artifact_name,
            "ref": self._ref_value,
            "type": self.__class__.__name__,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._artifact_name!r}, {self._ref_value!r})"
