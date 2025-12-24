"""Configuration settings with environment variable support."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class Settings:
    """Configuration settings for warpdatasets.

    Settings are loaded from environment variables with WARPDATASETS_ prefix,
    and can be overridden programmatically.
    """

    # Workspace root for local datasets
    # Layout: workspace_root/manifests/{workspace}/{name}/{version}.json
    #         workspace_root/data/{workspace}/{name}/{version}/...
    workspace_root: Path = field(
        default_factory=lambda: Path.home() / ".warpdatasets"
    )

    # Manifest store configuration
    # If None and mode is local, uses workspace_root for manifests
    manifest_base: str | None = None  # e.g., "s3://bucket/warp" or "https://host/warp"

    # Cache configuration
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "warpdatasets")

    # Mode configuration
    # Default is "auto": uses local workspace when manifest_base is not set
    mode: Literal["remote", "hybrid", "local", "auto"] = "auto"
    prefetch: Literal["off", "auto", "aggressive"] = "off"

    # Scope determines validation rules
    # - "local": Allow local://, relative paths, and external:// URIs
    # - "published": Strict validation, no local or external paths
    scope: Literal["local", "published"] = "local"

    # S3 configuration
    s3_region: str | None = None
    s3_endpoint_url: str | None = None  # For MinIO, LocalStack, etc.

    # Safety thresholds
    large_data_threshold: int = 1_000_000  # Rows before pandas guardrail kicks in
    large_shard_threshold: int = 10  # Number of shards before size warning

    # Development flags (deprecated, use scope instead)
    allow_file_manifests: bool = False

    def resolve_local_uri(self, uri: str) -> Path:
        """Resolve a local:// URI to an absolute path.

        Args:
            uri: URI in form local://path/to/file or relative path

        Returns:
            Absolute path resolved against workspace_root
        """
        if uri.startswith("local://"):
            relpath = uri[8:]  # Remove "local://"
        else:
            relpath = uri
        return self.workspace_root / relpath

    def is_local_mode(self) -> bool:
        """Check if operating in local mode."""
        return self.mode == "local" or (
            self.mode == "auto" and self.manifest_base is None
        )

    @property
    def effective_manifest_base(self) -> str:
        """Get effective manifest base, defaulting to workspace root for local mode."""
        if self.manifest_base is not None:
            return self.manifest_base
        if self.is_local_mode():
            return str(self.workspace_root)
        return ""

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings from environment variables."""
        # Determine workspace root
        workspace_root = Path(
            os.environ.get(
                "WARPDATASETS_WORKSPACE_ROOT",
                str(Path.home() / ".warpdatasets"),
            )
        )

        # Determine scope (defaults to local for frictionless local use)
        scope = os.environ.get("WARPDATASETS_SCOPE", "local")
        if scope not in ("local", "published"):
            scope = "local"

        # For backward compatibility, allow_file_manifests implies local scope
        allow_file_manifests = os.environ.get(
            "WARPDATASETS_ALLOW_FILE_MANIFESTS", ""
        ).lower() in ("1", "true", "yes")

        return cls(
            workspace_root=workspace_root,
            manifest_base=os.environ.get("WARPDATASETS_MANIFEST_BASE"),
            cache_dir=Path(
                os.environ.get(
                    "WARPDATASETS_CACHE_DIR",
                    str(Path.home() / ".cache" / "warpdatasets"),
                )
            ),
            mode=os.environ.get("WARPDATASETS_MODE", "auto"),  # type: ignore
            prefetch=os.environ.get("WARPDATASETS_PREFETCH", "off"),  # type: ignore
            scope=scope,  # type: ignore
            s3_region=os.environ.get("WARPDATASETS_S3_REGION")
            or os.environ.get("AWS_DEFAULT_REGION"),
            s3_endpoint_url=os.environ.get("WARPDATASETS_S3_ENDPOINT_URL"),
            large_data_threshold=int(
                os.environ.get("WARPDATASETS_LARGE_DATA_THRESHOLD", "1000000")
            ),
            allow_file_manifests=allow_file_manifests,
        )


# Global settings instance (lazy loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def configure(**kwargs) -> None:
    """Update global settings.

    Args:
        **kwargs: Settings to update
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_env()

    for key, value in kwargs.items():
        if hasattr(_settings, key):
            setattr(_settings, key, value)
        else:
            raise ValueError(f"Unknown setting: {key}")
