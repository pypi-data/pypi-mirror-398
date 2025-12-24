#!/usr/bin/env bash
set -euo pipefail

# Publish warpdatasets to PyPI.
# Usage:
#   ./publish.sh                        # Auto-increment patch version
#   PUBLISH_VERSION=3.0.0 ./publish.sh  # Set specific version

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env if present (exports PYPITOKEN into the environment)
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -o allexport
  source "${ROOT_DIR}/.env"
  set +o allexport
fi

: "${PYPITOKEN:?PYPITOKEN is required (set in .env or env)}"

cd "${ROOT_DIR}"

# Bump version in pyproject.toml and __init__.py
bump_version() {
  NEW_VERSION="$(
    PUBLISH_VERSION="${PUBLISH_VERSION:-}" python - <<'PY'
import os
import re
from pathlib import Path

pyproject = Path("pyproject.toml")
init_py = Path("warpdatasets/__init__.py")

py_text = pyproject.read_text()
match = re.search(r'^version\s*=\s*"([^"]+)"', py_text, flags=re.MULTILINE)
if not match:
    raise SystemExit("Could not find version in pyproject.toml")

current = match.group(1)
target = os.environ.get("PUBLISH_VERSION")
if not target:
    # Remove any alpha/beta/rc suffix for incrementing
    base = re.sub(r'[a-zA-Z]+\d*$', '', current)
    parts = base.split(".")
    while len(parts) < 3:
        parts.append("0")
    parts[-1] = str(int(parts[-1]) + 1)
    target = ".".join(parts)

# Update pyproject.toml version
py_text = re.sub(r'^version\s*=\s*"[^"]+"', f'version = "{target}"', py_text, flags=re.MULTILINE)
pyproject.write_text(py_text)

# Update __init__.py
if init_py.exists():
    init_text = init_py.read_text()
    init_text = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{target}"', init_text, flags=re.MULTILINE)
    init_py.write_text(init_text)

print(target)
PY
  )"
  echo "${NEW_VERSION}"
}

echo "=========================================="
echo "Publishing warpdatasets..."
echo "=========================================="

# Bump version
VERSION="$(bump_version)"
echo "Version set to ${VERSION}"

# Clean and build
rm -rf dist build *.egg-info
python -m build

# Upload
TWINE_USERNAME="__token__" TWINE_PASSWORD="${PYPITOKEN}" python -m twine upload dist/*

echo ""
echo "=========================================="
echo "warpdatasets ${VERSION} published!"
echo "=========================================="
