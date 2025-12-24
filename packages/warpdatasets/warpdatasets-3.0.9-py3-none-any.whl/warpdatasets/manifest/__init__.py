"""Manifest module - dataset version definitions."""

from warpdatasets.manifest.model import (
    ArtifactDescriptor,
    Binding,
    Manifest,
    ShardInfo,
    TableDescriptor,
)
from warpdatasets.manifest.canon import canonical_json, compute_version_hash
from warpdatasets.manifest.validate import validate_manifest, ValidationError

__all__ = [
    "Manifest",
    "TableDescriptor",
    "ShardInfo",
    "ArtifactDescriptor",
    "Binding",
    "canonical_json",
    "compute_version_hash",
    "validate_manifest",
    "ValidationError",
]
