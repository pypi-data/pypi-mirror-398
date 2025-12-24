"""Factory for creating typed refs based on media_type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from warpdatasets.refs.base import FileRef
from warpdatasets.refs.image import ImageRef
from warpdatasets.refs.audio import AudioRef

if TYPE_CHECKING:
    from warpdatasets.refs.base import ArtifactResolver


def create_ref(
    artifact_name: str,
    ref_value: str | None,
    media_type: str,
    resolver: "ArtifactResolver",
) -> FileRef | None:
    """Create a typed ref based on media_type.

    Args:
        artifact_name: Name of the artifact
        ref_value: Reference value (e.g., tar member path)
        media_type: Media type from binding ("image", "audio", "file")
        resolver: Resolver for fetching bytes

    Returns:
        Typed ref (ImageRef, AudioRef, or FileRef) or None if ref_value is empty.
    """
    # Handle None/empty values
    if ref_value is None or ref_value == "":
        return None

    # Select ref class based on media_type
    if media_type == "image":
        return ImageRef(
            artifact_name=artifact_name,
            ref_value=ref_value,
            resolver=resolver,
        )
    elif media_type == "audio":
        return AudioRef(
            artifact_name=artifact_name,
            ref_value=ref_value,
            resolver=resolver,
        )
    else:
        # Default to FileRef for "file" or unknown types
        return FileRef(
            artifact_name=artifact_name,
            ref_value=ref_value,
            resolver=resolver,
        )
