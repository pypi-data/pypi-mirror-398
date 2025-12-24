# WarpDatasets v3

Remote-first dataset library for ML training.

## Installation

```bash
pip install warpdatasets
```

## Quick Start

```python
import warpdatasets as wd

# Load a dataset
ds = wd.dataset("workspace/name")

# Get a table
table = ds.table("main")

# Preview data
print(table.head(5))

# Get schema
print(table.schema())
```

## CLI

```bash
# Show dataset info
warpdata info workspace/name

# Show schema
warpdata schema workspace/name

# Preview rows
warpdata head workspace/name -n 10
```
