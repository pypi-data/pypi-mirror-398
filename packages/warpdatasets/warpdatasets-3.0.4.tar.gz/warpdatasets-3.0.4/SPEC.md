# WarpDatasets v3 Specification

> **Status**: Locked specification for v3 implementation
> **Last Updated**: 2025-12-19

---

## Table of Contents

1. [Product Goals](#1-product-goals)
2. [Core Architecture Invariants](#2-core-architecture-invariants)
3. [Data Model](#3-data-model)
4. [Manifest Design](#4-manifest-design)
5. [Catalog & Registry](#5-catalog--registry)
6. [Execution & Engine](#6-execution--engine)
7. [Caching & Prefetch](#7-caching--prefetch)
8. [Publish Protocol](#8-publish-protocol)
9. [User API Contract](#9-user-api-contract)
10. [Error Handling & Diagnostics](#10-error-handling--diagnostics)
11. [Dependencies](#11-dependencies)
12. [Testing Requirements](#12-testing-requirements)
13. [Implementation Phases](#13-implementation-phases)

---

## 1. Product Goals

These goals are **non-negotiable** and drive all design decisions.

### G0 — Remote-First, Usable Without Pulling

A dataset must be queryable/streamable immediately after you know its ID. "Pulling" (downloading all shards) is **optional** and purely a performance optimization.

### G1 — Training-Friendly Throughput

The default path must support huge datasets efficiently:

- Parquet shard streaming via DuckDB range reads (S3/httpfs)
- Sharding for multi-worker training
- Background prefetch + caching (configurable) to reduce internet bottlenecks without blocking first step

### G2 — Raw Data is Reliable and Correctly Linked

"Raw data issues" are eliminated by design:

- No absolute path dependencies
- No "extract this dir and rewrite dataframe paths"
- Raw data access works remotely and locally with the same API

### G3 — Frictionless UX

The common workflow: user has `workspace/name`, runs generated loader or uses one-liners. Users shouldn't have to understand pulling, manifests, tar shards, S3 layouts, or registry internals.

---

## 2. Core Architecture Invariants

These constraints **must never be violated**. They prevent the "spaghetti" class of issues.

### I0 — Dataset Identity is Content-Addressed and Immutable

- A dataset version is defined by an **immutable manifest**
- Manifest must be canonicalized and its hash must be deterministic
- Once published, a version is **never mutated**; only "latest pointers" can change

> **Implication**: No version hash derived from `time.time()` or local state.

### I1 — No Canonical Local Paths in Manifests

**Manifests MAY store:**
- Blob hashes
- Remote URIs (s3/http) as locations
- Relative paths inside artifacts

**Manifests MUST NOT store:**
- `file:///home/user/...`
- Machine-specific directory roots
- Anything that breaks portability

> **Implication**: The system can run on any machine without rewriting stored values.

### I2 — Pull is Never Required for Correctness

- All core read APIs must work in "remote mode"
- Local caching is opportunistic; missing local cache must not break reads

### I3 — Raw Data is a First-Class Artifact Type

- Raw datasets (images/audio/video) are represented as **artifacts** in the manifest
- Tables link to raw artifacts via **references**, not absolute paths

### I4 — No Hidden Side Effects in Core Read Calls

Reading data **must not**:
- Modify the catalog/registry
- Trigger full downloads
- Extract directories

**Permitted implicit network IO:**
- Fetching small manifest metadata if missing/stale

Everything else must be explicit or lazily streamed.

---

## 3. Data Model

### 3.1 Payload Kinds (D0)

#### Tables (Structured, Columnar)
- **Format**: Parquet shards (canonical)
- **Read path**: Remote DuckDB scanning

#### Artifacts (Raw/Unstructured Payload)
- **Examples**: Images, audio, PDFs, videos, numpy arrays
- **Storage**: Shard blobs (recommended for scale)

### 3.2 Raw Storage Format (D1)

**Canonical raw artifact format**: Sharded archives

- Primary: tar shards (WebDataset-like)
- Optional: zstd compressed (`tar.zst`), or plain tar for random access

This is a Phase 0 decision because it determines how references are formed, how indexing works, and how caching behaves.

### 3.3 Table-to-Raw Linkage (D2)

A raw item in a table is stored as one of:

| Reference Type | Description |
|----------------|-------------|
| `member_path` | Reference into an artifact namespace (easiest) |
| `(shard_id, offset, length)` | Direct byte reference (fastest, requires index) |

> **Important**: Users never see these as low-level details. They see typed reference objects.

### 3.4 Typed Reference Objects (D3)

These are part of the **UX contract**:

```python
class FileRef:
    def open(self) -> IO[bytes]: ...
    def read_bytes(self) -> bytes: ...
    def local_path(self) -> Path: ...  # Downloads if needed

class ImageRef(FileRef):
    def as_pil(self) -> PIL.Image: ...
    def as_numpy(self) -> np.ndarray: ...

class AudioRef(FileRef):
    def as_array(self) -> np.ndarray: ...
    @property
    def sample_rate(self) -> int: ...
```

This preserves the "it just works" UX while fixing raw correctness.

---

## 4. Manifest Design

### 4.1 Manifest is Source of Truth (M0)

A dataset version is a manifest describing:

```yaml
dataset_id: workspace/name
version_hash: <deterministic hash>
tables:
  <table_name>:
    format: parquet
    shards: [<shard URIs/hashes>]
    schema: <optional arrow schema>
artifacts:
  <artifact_name>:
    kind: tar_shards | webdataset_shards
    shards: [<blob refs>]
    index: <optional index blob ref>
bindings:
  - table: <table_name>
    column: <column_name>
    artifact: <artifact_name>
    ref_type: file | image | audio
stats:
  row_count: <int>
  # ... other optional stats
```

### 4.2 Deterministic Version Hashing (M1)

```
version_hash = hash(canonical_manifest_json)
```

**Canonicalization rules:**
- Stable key ordering (sorted)
- Normalized numeric/string types
- No timestamps in hashed payload (timestamps can exist in a non-hashed "metadata" envelope)

### 4.3 Latest is a Pointer (M2)

- `latest.json` points to a version hash
- `latest.json` can change; version manifests **do not**

### 4.4 Manifests are Small and Cacheable (M3)

- Manifest fetch must be tiny and fast
- Cache manifests with `ETag` / `Last-Modified`

---

## 5. Catalog & Registry

### 5.1 Remote Catalog is Canonical (C0)

- Remote manifests are the **authoritative** dataset definitions
- Local registry (if any) is a performance cache/convenience, not required

### 5.2 Local Registry is Optional (C1)

If a local registry exists:

**It stores:**
- Dataset IDs
- Known versions
- Cached manifest metadata

**It does NOT store:**
- Canonical file paths to data resources
- Download state that drives correctness

### 5.3 No Cache Keys Based on URIs Alone (C2)

To prevent redownloading:

- Data blobs are cached by **content hash**, not "the URL that served it"
- Manifests are cached by `(dataset_id, version_hash)` and validated by ETag

> Once you have blob hash X locally, you don't re-download it unless evicted/corrupted.

---

## 6. Execution & Engine

### 6.1 DuckDB is Primary Engine (E0)

Remote scan via DuckDB is the main fast path:

```python
# Internal implementation
duckdb.read_parquet("s3://bucket/shard_*.parquet")
```

Features utilized:
- Projection pushdown
- Predicate pushdown
- Arrow streaming batches from relations

### 6.2 Arrow Batches are Primary Interface (E1)

Training pipelines consume:
- `Arrow RecordBatch` (fast path)
- `dict-of-lists` batches (convenience)

Pandas/Polars is **explicitly opt-in** and guarded for large datasets.

### 6.3 Sharding Semantics (E2)

```python
# Explicit sharding
Table.batches(shard=(rank, world_size))

# Auto-detect from environment
Table.batches(shard="auto")  # Reads RANK, WORLD_SIZE, LOCAL_RANK, etc.
```

Sharding is deterministic at the **shard-file level**.

---

## 7. Caching & Prefetch

### 7.1 Default Mode: Opportunistic, Non-Blocking (P0)

- Reads happen remotely
- Cache warms as a side effect
- **Never blocks** the first batch

### 7.2 Explicit Cache Warming (P1)

```bash
# CLI
warp warm ws/name --tables main --shards 0:50

# Python
dataset.warm(tables=["main"], max_bytes="200GB")
```

This replaces the ambiguous "pull" concept.

### 7.3 Cache Eviction Policy (P2)

- Content-addressed blob cache with size limit
- LRU/clock eviction policy
- Observable and controllable:

```bash
warp cache stats
warp cache gc --limit 500GB
```

---

## 8. Publish Protocol

### 8.1 Transactional and Idempotent (S0)

Publishing a version:

1. **Upload missing blobs** by hash (idempotent)
2. **Upload version manifest** (immutable)
3. **Update latest pointer** (mutable)

Raw artifacts use the **same mechanism** as tables.

### 8.2 Terminology (S1)

- Use **"publish"** not "sync"
- "Sync" implied mirroring local state
- In v3, the truth is the manifest graph

---

## 9. User API Contract

### 9.1 Primary Entrypoint (U0)

```python
import warpdatasets as wd

# Primary API
ds = wd.dataset("workspace/name")
table = ds.table("main")

# Compatibility (optional, later)
# df = wd.load("workspace/name")  # wrapper
```

### 9.2 Modes (U1)

```python
ds = wd.dataset("ws/name", mode="auto")  # Default
```

| Mode | Behavior |
|------|----------|
| `auto` | Remote-first, opportunistic caching, reasonable prefetch |
| `remote` | No local storage required |
| `hybrid` | Aggressive prefetch/cache |
| `local` | Offline mode; fail fast if missing |

### 9.3 Generated Loader (U2)

`warp init ws/name` generates:

```python
# ws_name_loader.py (generated)
import warpdatasets as wd

def get_dataset():
    return wd.dataset("ws/name")

def train_stream(batch_size=1000, shard="auto"):
    ds = get_dataset()
    for batch in ds.table("main").batches(batch_size, shard=shard):
        # Decode helpers for detected modalities
        yield batch

if __name__ == "__main__":
    # Smoke test
    for i, batch in enumerate(train_stream(batch_size=10)):
        print(f"Batch {i}: {len(batch)} rows")
        if i >= 2:
            break
    print("Smoke test passed!")
```

---

## 10. Error Handling & Diagnostics

### 10.1 Actionable, Typed Errors (X0)

| Error Type | Message Pattern |
|------------|-----------------|
| `AuthenticationError` | "AWS credentials not found. Set `AWS_PROFILE` or env vars..." |
| `PermissionError` | "Bucket policy forbids GetObject. Contact workspace admin..." |
| `DatasetNotFoundError` | "Dataset not published or wrong workspace/name. Check spelling..." |
| `ManifestCorruptedError` | "Manifest hash mismatch. Try `warp cache gc`..." |

### 10.2 Doctor Command (X1)

```bash
warp doctor
```

**Checks:**
- [ ] AWS/GCP credentials configured
- [ ] DuckDB httpfs/s3 extension available
- [ ] Small remote parquet range-read succeeds
- [ ] Cache directory writable
- [ ] Network connectivity to manifest store

**Output**: Actionable remediation steps for each failure.

---

## 11. Dependencies

### Core (Required)

| Package | Purpose |
|---------|---------|
| `duckdb` | Primary execution engine |
| `pyarrow` | Streaming interface, type system |

### Recommended

| Package | Purpose |
|---------|---------|
| `boto3` | S3 manifest operations (DuckDB also accesses S3) |

### Optional (Lazy Import)

| Package | Purpose |
|---------|---------|
| `Pillow` | Image decoding (`.as_pil()`) |
| `soundfile` / `librosa` | Audio decoding (`.as_array()`) |
| `pandas` | `.pandas()` export |
| `polars` | `.polars()` export |
| `torch` | `.to_torch()` wrapper (Phase 8+) |

---

## 12. Testing Requirements

These integration tests **enforce the architecture invariants**:

### Invariant Tests

```python
def test_remote_schema_no_pull():
    """Schema retrieval works without any downloads."""

def test_remote_stream_batches():
    """Streaming works without pull."""

def test_ref_open_remote():
    """ImageRef/FileRef .open() works remotely."""

def test_cache_no_redownload():
    """Same blob hash is not re-downloaded when cached."""

def test_publish_idempotent():
    """Publishing same version is a no-op."""
```

### Property Tests

- Manifest canonicalization is deterministic
- Version hash is stable across runs
- Sharding produces no duplicates across workers
- Sharding covers all rows exactly once

---

## 13. Implementation Phases

### Phase 1 — Core Primitives

**Goal**: Resolve dataset ID to manifest, query table data remotely without pull.

**Deliverables:**
- Manifest module (dataclasses/pydantic)
- Remote catalog resolver with ETag caching
- DuckDB remote scan adapter

**API Surface:**
```python
wd.dataset("ws/name") -> Dataset
Dataset.table("main") -> Table
Table.schema(), Table.head(n), Table.select(columns), Table.filter(expr)
```

**CLI:**
```bash
warp info ws/name
warp head ws/name -n 5
warp schema ws/name
```

**Exit Criteria:**
- [ ] Manifest resolves quickly
- [ ] Schema/head works without downloading full shards
- [ ] Filtered queries execute remotely through DuckDB

---

### Phase 2 — Streaming for Training

**Goal**: Streaming batches + distributed sharding, remote-first.

**Deliverables:**
- Arrow batch streaming
- Sharding semantics (`shard=(rank, world_size)`, `shard="auto"`)
- Basic observability (logging hooks)
- Safe defaults (guard `.pandas()` without limits)

**API Surface:**
```python
Table.batches(batch_size, columns=None, shard=None, limit=None)
Table.batch_dicts(...)  # dict-of-lists variant
```

**CLI:**
```bash
warp stream ws/name --batch-size 50000 --columns a,b --shard auto
```

**Exit Criteria:**
- [ ] Training loop starts immediately
- [ ] Scales across workers with no duplicates

---

### Phase 3 — Artifacts + Typed Refs

**Goal**: Robust raw data access without path rewriting, remote-first.

**Deliverables:**
- Artifact descriptors in manifest
- `FileRef`, `ImageRef`, `AudioRef` implementation
- Artifact resolver (remote streaming)
- Integration into `Table.batches()`

**API Surface:**
```python
batch["image"][0].as_pil()  # Just works
batch["audio"][0].as_array()
```

**CLI:**
```bash
warp inspect ws/name  # Shows tables, artifacts, bindings
warp cat ws/name --artifact raw_images --ref images/0001.jpg
```

**Exit Criteria:**
- [ ] `img = batch["image"][0].as_pil()` works remotely
- [ ] Raw data linked by manifest bindings, not machine paths

---

### Phase 4 — Caching + Prefetch

**Goal**: Improve throughput while preserving instant-start behavior.

**Deliverables:**
- Content-addressed blob cache
- Background prefetcher (non-blocking)
- Cache introspection and management

**API Surface:**
```python
Table.batches(..., prefetch="auto")  # Default
Dataset.warm(tables=["main"], max_bytes="200GB")
```

**CLI:**
```bash
warp cache stats
warp cache gc --limit 500GB
warp warm ws/name --tables main --shards 0:50
```

**Exit Criteria:**
- [ ] Streaming starts immediately
- [ ] Throughput improves as cache warms
- [ ] Users can warm caches without changing training code

---

### Phase 5 — Publish Pipeline

**Goal**: Transactional, idempotent publish that guarantees portability.

**Deliverables:**
- Dataset builder API
- Artifact packer (directory → tar shards)
- Publisher transaction

**API Surface:**
```python
from warpdatasets import DatasetBuilder

builder = DatasetBuilder("ws/name")
builder.add_table("main", parquet_files)
builder.add_artifact("raw_images", image_dir, kind="tar_shards")
builder.publish(set_latest=True)
```

**CLI:**
```bash
warp publish ws/name --table main=./data/*.parquet --artifact raw_images=./images/
warp publish ... --set-latest
warp list-remote ws/  # Fast, manifests only
```

**Exit Criteria:**
- [ ] Dataset publishable once, streamable immediately from any machine

---

### Phase 6 — Artifact Performance

**Goal**: Scale raw artifact access with minimal overhead.

**Deliverables:**
- Artifact index format (member → shard + offset + length)
- Ranged GET reads
- Multi-worker friendly behavior (avoid thundering herd)

**Exit Criteria:**
- [ ] Raw ref access doesn't require extracting archives
- [ ] Fast enough for training-scale throughput

---

### Phase 7 — Init Generator + Doctor

**Goal**: "It just works" UX with one command.

**Deliverables:**
- `warp init ws/name` code generator
- `warp doctor` diagnostics
- Minimal cookbook documentation

**Exit Criteria:**
- [ ] New user can run `warp init`, import generated file, start training

---

### Phase 8+ — Optional Modules

**After core is stable:**

#### Embeddings
- Vectors as tables (`vectors.parquet`)
- Derived artifacts (FAISS index)
- Publishable, cacheable, remote-readable

#### Torch Integration
```python
Dataset.to_torch(batch_size, shard="auto", prefetch="auto")
```

---

## Appendix A: Manifest JSON Schema (Draft)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["dataset_id", "version_hash", "tables"],
  "properties": {
    "dataset_id": {
      "type": "string",
      "pattern": "^[a-z0-9_-]+/[a-z0-9_-]+$"
    },
    "version_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "tables": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["format", "shards"],
        "properties": {
          "format": { "enum": ["parquet"] },
          "shards": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["uri", "hash"],
              "properties": {
                "uri": { "type": "string" },
                "hash": { "type": "string" },
                "row_count": { "type": "integer" },
                "byte_size": { "type": "integer" }
              }
            }
          },
          "schema": { "type": "object" }
        }
      }
    },
    "artifacts": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["kind", "shards"],
        "properties": {
          "kind": { "enum": ["tar_shards", "webdataset_shards"] },
          "shards": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["uri", "hash"],
              "properties": {
                "uri": { "type": "string" },
                "hash": { "type": "string" },
                "byte_size": { "type": "integer" }
              }
            }
          },
          "index": {
            "type": "object",
            "properties": {
              "uri": { "type": "string" },
              "hash": { "type": "string" }
            }
          }
        }
      }
    },
    "bindings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["table", "column", "artifact", "ref_type"],
        "properties": {
          "table": { "type": "string" },
          "column": { "type": "string" },
          "artifact": { "type": "string" },
          "ref_type": { "enum": ["file", "image", "audio", "video"] }
        }
      }
    },
    "stats": {
      "type": "object",
      "properties": {
        "total_rows": { "type": "integer" },
        "total_bytes": { "type": "integer" },
        "created_at": { "type": "string", "format": "date-time" }
      }
    },
    "metadata": {
      "type": "object",
      "description": "Non-hashed metadata envelope"
    }
  }
}
```

---

## Appendix B: Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `WARP_CACHE_DIR` | Local cache directory | `~/.cache/warpdatasets` |
| `WARP_CACHE_SIZE_GB` | Max cache size | `100` |
| `WARP_PREFETCH` | Default prefetch mode | `auto` |
| `WARP_MODE` | Default dataset mode | `auto` |
| `RANK` | Worker rank for sharding | - |
| `WORLD_SIZE` | Total workers for sharding | - |
| `LOCAL_RANK` | Local worker rank | - |

---

## Appendix C: CLI Command Reference

```
warp <command> [options]

Dataset Operations:
  info <dataset>              Show manifest and metadata
  schema <dataset>            Show table schema
  head <dataset> [-n N]       Preview first N rows
  stream <dataset>            Stream batches to stdout

Cache Operations:
  cache stats                 Show cache statistics
  cache gc [--limit GB]       Garbage collect cache
  warm <dataset>              Pre-warm cache

Publishing:
  publish <dataset>           Publish a dataset version
  list-remote <workspace/>    List published datasets

Utilities:
  init <dataset>              Generate loader code
  doctor                      Check environment health
  inspect <dataset>           Show tables, artifacts, bindings
```
