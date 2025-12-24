"""Canonical JSON serialization and version hashing.

Ensures deterministic serialization for content-addressed manifests:
- Keys are sorted lexicographically
- No whitespace
- Stable numeric formatting
- No NaN/Infinity values
- UTF-8 encoding
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def _check_value(value: Any, path: str = "") -> None:
    """Check that a value can be safely serialized to JSON."""
    if isinstance(value, float):
        if math.isnan(value):
            raise ValueError(f"NaN value at {path} is not JSON serializable")
        if math.isinf(value):
            raise ValueError(f"Infinity value at {path} is not JSON serializable")
    elif isinstance(value, dict):
        for k, v in value.items():
            _check_value(v, f"{path}.{k}" if path else k)
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _check_value(v, f"{path}[{i}]")


def canonical_json(obj: dict[str, Any]) -> bytes:
    """Serialize object to canonical JSON bytes.

    Properties:
    - Keys are sorted lexicographically at all levels
    - No whitespace between elements
    - UTF-8 encoded
    - Raises ValueError for NaN or Infinity floats

    Args:
        obj: Dictionary to serialize

    Returns:
        UTF-8 encoded JSON bytes

    Raises:
        ValueError: If obj contains NaN or Infinity values
    """
    # Validate no NaN/Infinity
    _check_value(obj)

    # Serialize with sorted keys and no whitespace
    json_str = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,  # Extra safety
    )

    return json_str.encode("utf-8")


def compute_version_hash(manifest_dict: dict[str, Any]) -> str:
    """Compute deterministic version hash from manifest dictionary.

    The hash is computed from the canonical JSON representation,
    excluding 'meta' and 'locations' envelopes if present.

    - 'meta' is non-hashed metadata (created_at, etc.)
    - 'locations' is non-hashed location hints (s3://, local://, etc.)

    Args:
        manifest_dict: Manifest as dictionary (may include 'meta', 'locations')

    Returns:
        First 16 characters of SHA-256 hex digest
    """
    # Remove 'meta' and 'locations' from hashing if present
    # These fields are operational, not content-defining
    hashable = {k: v for k, v in manifest_dict.items() if k not in ("meta", "locations")}

    canonical = canonical_json(hashable)
    full_hash = hashlib.sha256(canonical).hexdigest()

    return full_hash[:16]
