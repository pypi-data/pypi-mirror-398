"""Manifest validation.

Enforces invariants:
- I1.4: Manifest contains no machine-specific absolute local paths
- I3.1: Raw data is represented as artifacts, not paths
- I3.4: Bindings are deterministic and dataset-version scoped
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from warpdatasets.manifest.model import Manifest

# Known artifact kinds
# - tar_shards: Tar archives for remote-optimized access
# - directory: Local directory for frictionless local iteration
KNOWN_ARTIFACT_KINDS = {"tar_shards", "directory"}

# Known ref types and their compatible artifact kinds
REF_TYPE_ARTIFACT_COMPATIBILITY = {
    "tar_member_path": {"tar_shards"},
    "file_path": {"directory"},  # For directory artifacts
}

# Known media types
KNOWN_MEDIA_TYPES = {"image", "audio", "file"}


@dataclass
class ValidationIssue:
    """A single validation issue."""

    message: str
    location: str | None = None
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        if self.location:
            return f"[{self.severity.upper()}] {self.location}: {self.message}"
        return f"[{self.severity.upper()}] {self.message}"


class ValidationError(Exception):
    """Raised when manifest validation fails."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        message = self._format_message()
        super().__init__(message)

    def _format_message(self) -> str:
        lines = ["Manifest validation failed:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


# URI schemes by scope
# - Remote schemes: Always allowed (portable)
# - Local schemes: Only allowed in local scope
REMOTE_SCHEMES = {"s3", "http", "https", "gs"}  # gs for GCS
LOCAL_SCHEMES = {"local", "file", "external"}  # local://, file://, external://

# Dataset ID pattern: workspace/name with alphanumeric, underscore, hyphen
DATASET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$")


def _get_scope() -> Literal["local", "published"]:
    """Get validation scope from environment or settings."""
    scope = os.environ.get("WARPDATASETS_SCOPE", "local")
    if scope not in ("local", "published"):
        scope = "local"
    return scope  # type: ignore


def _allow_file_uris() -> bool:
    """Check if file:// URIs are allowed (deprecated, use scope instead)."""
    # Check explicit flag first (backward compatibility)
    if os.environ.get("WARPDATASETS_ALLOW_FILE_MANIFESTS", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True
    # In local scope, allow file URIs
    return _get_scope() == "local"


def validate_manifest(
    manifest: Manifest,
    *,
    allow_file_uris: bool = False,
    scope: Literal["local", "published"] | None = None,
) -> None:
    """Validate a manifest against all invariants.

    Args:
        manifest: The manifest to validate
        allow_file_uris: If True, allow file:// URIs (deprecated, use scope)
        scope: Validation scope - "local" allows local://, "published" is strict

    Raises:
        ValidationError: If validation fails, containing all issues found
    """
    issues: list[ValidationIssue] = []

    # Determine effective scope
    scope_from_env = scope is None
    if scope is None:
        scope = _get_scope()

    # Check file URI permission (local scope or explicit flag)
    # Only check _allow_file_uris() if scope wasn't explicitly provided
    local_uris_allowed = (
        scope == "local"
        or allow_file_uris
        or (scope_from_env and _allow_file_uris())
    )

    # Validate dataset ID format
    if not manifest.dataset:
        issues.append(ValidationIssue(
            message="Dataset ID is empty",
            location="dataset",
        ))
    elif not DATASET_ID_PATTERN.match(manifest.dataset):
        issues.append(ValidationIssue(
            message=f"Dataset ID '{manifest.dataset}' must be in 'workspace/name' format",
            location="dataset",
        ))

    # Validate tables exist
    if not manifest.tables:
        issues.append(ValidationIssue(
            message="Manifest must have at least one table",
            location="tables",
        ))
    else:
        # Validate 'main' table exists
        if "main" not in manifest.tables:
            issues.append(ValidationIssue(
                message="Manifest must have a 'main' table",
                location="tables",
            ))

        # Validate each table
        for table_name, table in manifest.tables.items():
            table_loc = f"tables.{table_name}"

            # Validate format
            if table.format != "parquet":
                issues.append(ValidationIssue(
                    message=f"Table format must be 'parquet', got '{table.format}'",
                    location=f"{table_loc}.format",
                ))

            # Validate shards - each must have either uri or key
            for i, shard in enumerate(table.shards):
                shard_loc = f"{table_loc}.shards[{i}]"

                if shard.uri is None and shard.key is None:
                    issues.append(ValidationIssue(
                        message="Shard must have either 'uri' or 'key'",
                        location=shard_loc,
                    ))
                elif shard.uri is not None:
                    # Legacy URI-based shard - validate the URI
                    uri_issues = _validate_uri(
                        shard.uri,
                        shard_loc,
                        local_uris_allowed,
                    )
                    issues.extend(uri_issues)
                # key-based shards are always valid (resolved against locations)

    # Validate artifacts
    for artifact_name, artifact in manifest.artifacts.items():
        artifact_loc = f"artifacts.{artifact_name}"

        # Validate kind
        if artifact.kind not in KNOWN_ARTIFACT_KINDS:
            issues.append(ValidationIssue(
                message=f"Unknown artifact kind '{artifact.kind}'. Known kinds: {', '.join(sorted(KNOWN_ARTIFACT_KINDS))}",
                location=f"{artifact_loc}.kind",
            ))

        # Validate shards non-empty
        if not artifact.shards:
            issues.append(ValidationIssue(
                message="Artifact must have at least one shard",
                location=f"{artifact_loc}.shards",
            ))

        # Validate shards - each must have either uri or key
        for i, shard in enumerate(artifact.shards):
            shard_loc = f"{artifact_loc}.shards[{i}]"

            if shard.uri is None and shard.key is None:
                issues.append(ValidationIssue(
                    message="Shard must have either 'uri' or 'key'",
                    location=shard_loc,
                ))
            elif shard.uri is not None:
                # Legacy URI-based shard - validate the URI
                uri_issues = _validate_uri(
                    shard.uri,
                    shard_loc,
                    local_uris_allowed,
                )
                issues.extend(uri_issues)
            # key-based shards are always valid (resolved against locations)

    # Validate bindings
    for i, binding in enumerate(manifest.bindings):
        binding_loc = f"bindings[{i}]"

        # Validate table exists
        if binding.table not in manifest.tables:
            issues.append(ValidationIssue(
                message=f"Binding references non-existent table '{binding.table}'",
                location=f"{binding_loc}.table",
            ))

        # Validate artifact exists
        if binding.artifact not in manifest.artifacts:
            issues.append(ValidationIssue(
                message=f"Binding references non-existent artifact '{binding.artifact}'",
                location=f"{binding_loc}.artifact",
            ))

        # Validate ref_type is known and compatible with artifact kind
        if binding.ref_type not in REF_TYPE_ARTIFACT_COMPATIBILITY:
            issues.append(ValidationIssue(
                message=f"Unknown ref_type '{binding.ref_type}'. Known types: {', '.join(sorted(REF_TYPE_ARTIFACT_COMPATIBILITY.keys()))}",
                location=f"{binding_loc}.ref_type",
            ))
        elif binding.artifact in manifest.artifacts:
            artifact = manifest.artifacts[binding.artifact]
            compatible_kinds = REF_TYPE_ARTIFACT_COMPATIBILITY[binding.ref_type]
            if artifact.kind not in compatible_kinds:
                issues.append(ValidationIssue(
                    message=f"ref_type '{binding.ref_type}' is not compatible with artifact kind '{artifact.kind}'",
                    location=f"{binding_loc}.ref_type",
                ))

        # Validate media_type
        if binding.media_type not in KNOWN_MEDIA_TYPES:
            issues.append(ValidationIssue(
                message=f"Unknown media_type '{binding.media_type}'. Known types: {', '.join(sorted(KNOWN_MEDIA_TYPES))}",
                location=f"{binding_loc}.media_type",
            ))

    # Validate locations (if present)
    for i, location in enumerate(manifest.locations):
        loc_loc = f"locations[{i}]"
        loc_issues = _validate_location(location, loc_loc, local_uris_allowed)
        issues.extend(loc_issues)

    if issues:
        raise ValidationError(issues)


def _validate_location(
    location: str,
    loc_path: str,
    local_uris_allowed: bool,
) -> list[ValidationIssue]:
    """Validate a manifest location entry.

    Args:
        location: The location URI to validate
        loc_path: Location in manifest for error messages
        local_uris_allowed: Whether local:// URIs are allowed

    Returns:
        List of validation issues found
    """
    issues: list[ValidationIssue] = []

    # Parse the location
    try:
        parsed = urlparse(location)
    except Exception as e:
        issues.append(ValidationIssue(
            message=f"Invalid location URI '{location}': {e}",
            location=loc_path,
        ))
        return issues

    scheme = parsed.scheme.lower()

    # Check for missing scheme
    if not scheme:
        issues.append(ValidationIssue(
            message=f"Location '{location}' is missing a scheme",
            location=loc_path,
        ))
        return issues

    # Check for local schemes
    if scheme in LOCAL_SCHEMES:
        if not local_uris_allowed:
            issues.append(ValidationIssue(
                message=(
                    f"Local location scheme '{scheme}://' is not allowed in published manifests: '{location}'"
                ),
                location=loc_path,
            ))
        return issues

    # Check for remote schemes
    if scheme not in REMOTE_SCHEMES:
        all_schemes = REMOTE_SCHEMES | (LOCAL_SCHEMES if local_uris_allowed else set())
        issues.append(ValidationIssue(
            message=f"Location scheme '{scheme}' is not supported. Allowed: {', '.join(sorted(all_schemes))}",
            location=loc_path,
        ))

    return issues


def _validate_uri(
    uri: str,
    location: str,
    local_uris_allowed: bool,
) -> list[ValidationIssue]:
    """Validate a single URI.

    Args:
        uri: The URI to validate
        location: Location in manifest for error messages
        local_uris_allowed: Whether local:// and file:// schemes are allowed

    Returns:
        List of validation issues found
    """
    issues: list[ValidationIssue] = []

    # Try to parse the URI
    try:
        parsed = urlparse(uri)
    except Exception as e:
        issues.append(ValidationIssue(
            message=f"Invalid URI '{uri}': {e}",
            location=location,
        ))
        return issues

    scheme = parsed.scheme.lower()

    # Check for missing scheme - allow relative paths in local scope
    if not scheme:
        if local_uris_allowed:
            # Relative paths are OK in local scope (resolved against workspace_root)
            return issues
        issues.append(ValidationIssue(
            message=f"URI '{uri}' is missing a scheme (expected s3://, https://, etc.)",
            location=location,
        ))
        return issues

    # Check for local schemes (local://, file://, external://)
    if scheme in LOCAL_SCHEMES:
        if not local_uris_allowed:
            issues.append(ValidationIssue(
                message=(
                    f"Local URI scheme '{scheme}://' is not allowed in published manifests: '{uri}'. "
                    "Use scope='local' or WARPDATASETS_SCOPE=local for local development."
                ),
                location=location,
            ))
        return issues

    # Check for remote schemes
    if scheme not in REMOTE_SCHEMES:
        all_schemes = REMOTE_SCHEMES | (LOCAL_SCHEMES if local_uris_allowed else set())
        issues.append(ValidationIssue(
            message=f"URI scheme '{scheme}' is not supported. Allowed: {', '.join(sorted(all_schemes))}",
            location=location,
        ))

    return issues
