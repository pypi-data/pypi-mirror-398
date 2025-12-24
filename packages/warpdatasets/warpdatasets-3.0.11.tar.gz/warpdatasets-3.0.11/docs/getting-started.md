# Getting Started with WarpDatasets

A simple dataset registry for ML workflows. Manage datasets locally, publish to S3, load anywhere.

## Installation

```bash
pip install -e .
```

## Quick Start

### 1. Load a dataset

```python
import warpdatasets as wd

ds = wd.dataset("vision/my-dataset")

# Iterate rows
for row in ds.rows():
    print(row)
    break

# Load images/artifacts
for batch in ds.table("main").batches(batch_size=8, as_format="dict", wrap_refs=True):
    img_ref = batch["image"][0]
    data = img_ref.read_bytes()  # or img_ref.as_pil()
```

### 2. Register a dataset

```bash
# Parquet only (tabular data)
warpdata register myworkspace/mydataset \
  --table main=/path/to/data.parquet

# With image artifacts
warpdata register vision/cats-dogs \
  --table main=/path/to/metadata.parquet \
  --artifact images=/path/to/images:image
```

**Important:** Parquet columns must contain relative filenames (not absolute paths), and column names must match artifact names.

### 3. Publish to S3

```bash
warpdata publish myworkspace/mydataset
```

### 4. Use on another machine

```bash
warpdata sync pull
```

```python
import warpdatasets as wd
ds = wd.dataset("myworkspace/mydataset")  # Just works
```

## Modes

WarpDatasets has different modes for loading remote data:

| Mode | Behavior |
|------|----------|
| `strict` (default) | Downloads ALL shards on first access, then local reads |
| `hybrid` | Downloads shards lazily as accessed |
| `remote` | Streams directly from S3 (slow, no caching) |
| `local` | Only uses local files, fails if not present |

Set via environment variable:
```bash
export WARPDATASETS_MODE=hybrid
```

## CLI Commands

```bash
warpdata register   # Register a new dataset
warpdata publish    # Publish to S3
warpdata sync pull  # Pull manifests from S3
warpdata sync push  # Push manifests to S3
warpdata ls         # List datasets
warpdata info       # Show dataset info
warpdata inspect    # Detailed inspection
```

## Project Structure

```
~/.warpdatasets/
├── manifests/           # Dataset manifests (JSON)
│   └── workspace/
│       └── dataset/
│           ├── {version}.json
│           └── latest.json
└── data/                # Cached data shards
    └── workspace/
        └── dataset/
            └── {version}/
                └── ...
```

## Next Steps

- See [adding-datasets.md](adding-datasets.md) for detailed examples
- Run `warpdata --help` for all CLI options
