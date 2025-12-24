"""warpdata cat command - output artifact member bytes."""

from __future__ import annotations

import sys
from argparse import Namespace

import warpdatasets as wd
from warpdatasets.artifacts.resolver import ArtifactResolver
from warpdatasets.util.errors import RefNotFoundError, WarpDatasetsError


def run(args: Namespace) -> int:
    """Run the cat command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        ds = wd.dataset(args.dataset, version=args.ds_version)
    except WarpDatasetsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Check artifact exists
    if args.artifact not in ds.manifest.artifacts:
        available = ", ".join(ds.manifest.artifacts.keys()) or "(none)"
        print(f"Error: Artifact '{args.artifact}' not found. Available: {available}",
              file=sys.stderr)
        return 1

    # Create resolver
    resolver = ArtifactResolver(ds.manifest)

    try:
        data = resolver.read_bytes(args.artifact, args.ref)
    except RefNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Output mode
    if args.info:
        # Print info about the ref
        print(f"Artifact: {args.artifact}")
        print(f"Ref: {args.ref}")
        print(f"Size: {len(data):,} bytes")

        # Try to detect content type
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            print("Type: PNG image")
        elif data[:2] == b'\xff\xd8':
            print("Type: JPEG image")
        elif data[:4] == b'RIFF' and data[8:12] == b'WAVE':
            print("Type: WAV audio")
        else:
            print("Type: binary")

    elif args.show_image:
        # Try to display image
        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(data))
            print(f"Image: {img.size[0]}x{img.size[1]}, mode={img.mode}")

            # If terminal supports it, could show with external viewer
            # For now just show info
            if args.output:
                with open(args.output, "wb") as f:
                    f.write(data)
                print(f"Saved to: {args.output}")
        except ImportError:
            print("Error: Pillow required for --show-image", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error decoding image: {e}", file=sys.stderr)
            return 1

    elif args.output:
        # Write to file
        with open(args.output, "wb") as f:
            f.write(data)
        print(f"Saved {len(data):,} bytes to: {args.output}")

    else:
        # Write raw bytes to stdout
        sys.stdout.buffer.write(data)

    return 0
