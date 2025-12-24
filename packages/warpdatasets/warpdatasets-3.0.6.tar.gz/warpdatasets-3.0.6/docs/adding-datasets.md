# Adding Datasets to WarpDatasets

This guide covers how to add datasets to warpdatasets using the canonical workflow.

## Overview

There are two types of datasets:

1. **Parquet-only** - Pure tabular data (no binary files like images/audio)
2. **With artifacts** - Tabular metadata + binary files (images, audio, etc.)

## Prerequisites

```bash
# Ensure you have warpdatasets installed
pip install -e .

# Verify CLI works
warpdata --help
```

## 1. Parquet-Only Datasets

For datasets that are purely tabular (CSV, JSON → Parquet):

### Step 1: Prepare your parquet file(s)

```python
import pandas as pd

df = pd.read_csv("my_data.csv")
df.to_parquet("my_data.parquet", index=False)
```

### Step 2: Register the dataset

```bash
warpdata register myworkspace/mydataset \
  --table main=/path/to/my_data.parquet
```

### Step 3: Publish to S3

```bash
warpdata publish myworkspace/mydataset
```

### Example: Simple text dataset

```bash
# Register
warpdata register nlp/quotes \
  --table main=/data/quotes.parquet

# Publish
warpdata publish nlp/quotes
```

## 2. Datasets with Artifacts (Images, Audio, etc.)

For datasets with binary files, you need:
- A parquet file with metadata
- Directory(ies) containing the binary files
- Column names that **match artifact names**

### Step 1: Organize your data

```
my_dataset/
├── metadata.parquet    # Has columns: id, label, train_images, train_labels
├── train_images/       # Directory with image files
│   ├── 001.jpg
│   ├── 002.jpg
│   └── ...
└── train_labels/       # Directory with label files
    ├── 001.png
    ├── 002.png
    └── ...
```

### Step 2: Create parquet with RELATIVE paths

**IMPORTANT**: The parquet columns must contain **relative filenames** (not absolute paths).

```python
import pandas as pd
from pathlib import Path

# Create metadata with RELATIVE paths
df = pd.DataFrame({
    "id": [1, 2, 3],
    "label": ["cat", "dog", "cat"],
    # Column name MUST match artifact name
    "train_images": ["001.jpg", "002.jpg", "003.jpg"],  # Relative!
    "train_labels": ["001.png", "002.png", "003.png"],  # Relative!
})

df.to_parquet("my_dataset/metadata.parquet", index=False)
```

**Column naming rule**: If your artifact is named `train_images`, your parquet column must also be named `train_images`.

### Step 3: Register with artifacts

```bash
warpdata register vision/mydataset \
  --table main=/path/to/metadata.parquet \
  --artifact train_images=/path/to/train_images:image \
  --artifact train_labels=/path/to/train_labels:image
```

Artifact format: `name=/path/to/directory:media_type`

Media types:
- `image` - Images (jpg, png, tif, etc.)
- `audio` - Audio files (wav, mp3, etc.)
- `file` - Generic binary files

### Step 4: Publish

```bash
warpdata publish vision/mydataset
```

This will:
1. Pack directories into tar shards
2. Build artifact indices for S3 range reads
3. Upload everything to S3
4. Create a portable manifest

## Complete Example: Vision Dataset

```bash
# 1. Prepare data structure
ls ~/data/cats_dogs/
# metadata.parquet  train_images/  train_labels/

# 2. Verify parquet has relative paths
python -c "
import pandas as pd
df = pd.read_parquet('~/data/cats_dogs/metadata.parquet')
print(df[['train_images', 'train_labels']].head())
"
#   train_images  train_labels
# 0      001.jpg       001.png
# 1      002.jpg       002.png

# 3. Register
warpdata register vision/cats-dogs \
  --table main=~/data/cats_dogs/metadata.parquet \
  --artifact train_images=~/data/cats_dogs/train_images:image \
  --artifact train_labels=~/data/cats_dogs/train_labels:image

# 4. Verify registration
warpdata info vision/cats-dogs
warpdata inspect vision/cats-dogs

# 5. Publish to S3
warpdata publish vision/cats-dogs

# 6. Verify on another machine
warpdata sync pull
python -c "
import warpdatasets as wd
ds = wd.dataset('vision/cats-dogs')
for batch in ds.table('main').batches(batch_size=1, as_format='dict', wrap_refs=True):
    img_ref = batch['train_images'][0]
    data = img_ref.read_bytes()
    print(f'Read {len(data)} bytes')
    break
"
```

## Verification Checklist

After publishing, verify on a fresh machine:

```bash
# 1. Clear local state
rm -rf ~/.warpdatasets

# 2. Pull manifest
warpdata sync pull

# 3. Check dataset info
warpdata info myworkspace/mydataset
warpdata inspect myworkspace/mydataset

# 4. Test loading
python -c "
import warpdatasets as wd
ds = wd.dataset('myworkspace/mydataset')

# For parquet-only
for row in ds.rows():
    print(row)
    break

# For datasets with artifacts
for batch in ds.table('main').batches(batch_size=1, as_format='dict', wrap_refs=True):
    ref = batch['my_artifact_column'][0]
    data = ref.read_bytes()
    print(f'Read {len(data)} bytes')
    break
"
```

## Common Mistakes

### 1. Absolute paths in parquet

**Wrong:**
```python
df["train_images"] = "/home/user/data/train_images/001.jpg"
```

**Correct:**
```python
df["train_images"] = "001.jpg"
```

### 2. Column name doesn't match artifact name

**Wrong:**
```bash
# Parquet has column "image_path" but artifact is "train_images"
warpdata register ... --artifact train_images=/path/to/images
```

**Correct:**
```bash
# Parquet column "train_images" matches artifact name "train_images"
warpdata register ... --artifact train_images=/path/to/images
```

### 3. Forgetting media type

**Wrong:**
```bash
--artifact train_images=/path/to/images
```

**Correct:**
```bash
--artifact train_images=/path/to/images:image
```

## Troubleshooting

### "Ref not found" errors

Check that:
1. Parquet column values are relative paths (just filenames)
2. Files exist in the artifact directory with matching names
3. Column name matches artifact name

### "No index" errors for remote datasets

The publish step should automatically build indices. If missing:
1. Re-register the dataset
2. Re-publish

### Slow loading

Ensure artifacts have indices. Check with:
```bash
warpdata inspect myworkspace/mydataset
# Should show "Has index: yes" for each artifact
```
