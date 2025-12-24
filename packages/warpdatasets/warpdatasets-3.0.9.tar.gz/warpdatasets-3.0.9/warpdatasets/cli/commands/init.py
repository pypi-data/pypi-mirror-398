"""warpdata init command - generate dataset loader.

Generates a runnable Python file tailored to a specific dataset.
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import warpdatasets as wd
from warpdatasets.tools.initgen import (
    LoaderGenerator,
    dataset_id_to_filename,
)
from warpdatasets.util.errors import WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the init command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    dataset_id = args.dataset

    # Load the dataset to get manifest
    try:
        ds = wd.dataset(dataset_id, version=args.ds_version)
    except WarpDatasetsError as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create generator
    generator = LoaderGenerator(
        manifest=ds.manifest,
        version=ds.manifest.version_hash[:12] if hasattr(ds.manifest, "version_hash") else None,
        table=args.table,
        mode=args.mode,
        prefetch=args.prefetch,
        include_refs=args.include_refs,
        columns=args.columns.split(",") if args.columns else None,
    )

    # Generate code
    code = generator.generate()

    # Handle output
    if args.print:
        print(code)
        return 0

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(dataset_id_to_filename(dataset_id))

    # Check if exists
    if output_path.exists() and not args.force:
        print(f"File already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    # Write file
    output_path.write_text(code)

    print(f"Generated: {output_path}")
    print()
    print("Usage:")
    print(f"  python {output_path}        # Verify dataset access")
    print(f"  from {output_path.stem} import stream_batches")
    print()

    # Show analysis
    analysis = generator.analysis
    table_analysis = analysis.tables.get(args.table)

    if table_analysis:
        if table_analysis.has_bindings:
            print(f"Ref columns: {', '.join(table_analysis.ref_columns)}")
            print("Helper functions generated for decoding refs.")
        else:
            print("No bindings found - pure tabular data.")
    print()

    return 0
