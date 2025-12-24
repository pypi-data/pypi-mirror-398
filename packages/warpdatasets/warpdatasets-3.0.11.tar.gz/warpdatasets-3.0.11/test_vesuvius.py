#!/usr/bin/env python3
"""Test script for vesuvius-scrolls dataset loading.

Run this to verify the dataset loads correctly and data is accessible.
"""

import sys
from pathlib import Path

# Add the local package to path for testing
sys.path.insert(0, str(Path(__file__).parent))

import warpdatasets as wd


def main():
    print("=" * 60)
    print("Vesuvius Scrolls Dataset Test")
    print("=" * 60)

    # 1. Load the dataset
    print("\n[1] Loading dataset...")
    try:
        ds = wd.dataset("vision/vesuvius-scrolls")
        print(f"    Dataset: {ds.id}")
        print(f"    Version: {ds.version_hash}")
    except Exception as e:
        print(f"    ERROR: Failed to load dataset: {e}")
        return 1

    # 2. Show manifest info
    print("\n[2] Manifest info...")
    try:
        manifest = ds.manifest
        print(f"    Tables: {list(manifest.tables.keys())}")
        print(f"    Artifacts: {list(manifest.artifacts.keys())}")
        print(f"    Bindings: {len(manifest.bindings)}")
        print(f"    Locations: {manifest.locations if manifest.locations else 'None (legacy)'}")
        print(f"    Is portable: {manifest.is_portable}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 3. Check main table
    print("\n[3] Main table info...")
    try:
        main_table = ds.table("main")
        print(f"    Row count: {main_table.row_count}")
        print(f"    Shard count: {main_table.shard_count}")

        # Show shards info
        for i, shard in enumerate(main_table.descriptor.shards[:3]):
            if shard.key:
                print(f"    Shard {i}: key={shard.key}")
            elif shard.uri:
                uri_short = shard.uri[:60] + "..." if len(shard.uri) > 60 else shard.uri
                print(f"    Shard {i}: uri={uri_short}")
        if main_table.shard_count > 3:
            print(f"    ... and {main_table.shard_count - 3} more shards")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 4. Get schema
    print("\n[4] Schema...")
    try:
        schema = main_table.schema()
        for col, dtype in list(schema.items())[:10]:
            print(f"    {col}: {dtype}")
        if len(schema) > 10:
            print(f"    ... and {len(schema) - 10} more columns")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 5. Preview data (head)
    print("\n[5] Preview (head 5 rows)...")
    try:
        head_df = main_table.head(5).fetchdf()
        print(head_df.to_string(max_colwidth=50))
    except Exception as e:
        print(f"    ERROR: {e}")

    # 6. Stream a small batch
    print("\n[6] Streaming test (1 batch of 10 rows)...")
    try:
        batch_count = 0
        row_count = 0
        for batch in main_table.batches(batch_size=10, limit=10):
            batch_count += 1
            row_count += len(batch)
            print(f"    Batch {batch_count}: {len(batch)} rows")
            # Show columns
            if hasattr(batch, 'column_names'):
                print(f"    Columns: {batch.column_names}")
            break  # Just one batch
        print(f"    Total: {row_count} rows in {batch_count} batch(es)")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 7. Iterate rows
    print("\n[7] Row iteration test (3 rows)...")
    try:
        count = 0
        for row in ds.rows():
            print(f"    Row {count}:")
            for k, v in row.items():
                val_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                print(f"      {k}: {val_str}")
            count += 1
            if count >= 3:
                break
    except Exception as e:
        print(f"    ERROR: {e}")

    # 8. Check artifacts
    print("\n[8] Artifacts...")
    try:
        if manifest.artifacts:
            for name, artifact in manifest.artifacts.items():
                print(f"    {name}:")
                print(f"      Kind: {artifact.kind}")
                print(f"      Shards: {len(artifact.shards)}")
                print(f"      Is portable: {artifact.is_portable}")
                if artifact.index:
                    print(f"      Has index: yes")
        else:
            print("    No artifacts in this dataset")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 9. Check bindings
    print("\n[9] Bindings...")
    try:
        if manifest.bindings:
            for binding in manifest.bindings[:5]:
                print(f"    {binding.table}.{binding.column} -> {binding.artifact} ({binding.media_type})")
            if len(manifest.bindings) > 5:
                print(f"    ... and {len(manifest.bindings) - 5} more bindings")
        else:
            print("    No bindings in this dataset")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 10. Check addons/embeddings
    print("\n[10] Addons/Embeddings...")
    try:
        if manifest.addons:
            for name, addon in manifest.addons.items():
                print(f"    {name}: {addon.kind}")
        else:
            print("    No addons found")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 11. Try to actually load an image from artifacts
    print("\n[11] Image loading test (via artifacts)...")
    try:
        # Get first batch with wrap_refs to decode artifact references
        for batch in main_table.batches(batch_size=1, limit=1, as_format="dict", wrap_refs=True):
            print(f"    Batch keys: {list(batch.keys())}")

            # Check train_images column
            if "train_images" in batch:
                ref = batch["train_images"][0]
                print(f"    train_images type: {type(ref).__name__}")
                print(f"    train_images value: {ref}")

                # If it's a Ref object, try to read it
                if hasattr(ref, 'read_bytes'):
                    print("    Attempting to read bytes from S3...")
                    data = ref.read_bytes()
                    print(f"    SUCCESS! Read {len(data)} bytes from image artifact!")

                    # Try to decode as image
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(data))
                        print(f"    Image size: {img.size}, mode: {img.mode}")
                    except ImportError:
                        print("    (PIL not installed - can't decode image)")
                    except Exception as e:
                        print(f"    Image decode failed: {e}")
                elif hasattr(ref, 'as_pil'):
                    # Try ImageRef.as_pil() directly
                    print("    Attempting as_pil()...")
                    img = ref.as_pil()
                    print(f"    SUCCESS! Image size: {img.size}, mode: {img.mode}")
                else:
                    print(f"    Not a ref object, raw value: {str(ref)[:80]}...")
            break
    except Exception as e:
        import traceback
        print(f"    ERROR: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
