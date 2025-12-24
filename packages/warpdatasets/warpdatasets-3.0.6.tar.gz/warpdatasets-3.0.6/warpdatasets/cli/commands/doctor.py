"""warpdata doctor command - diagnose environment issues.

Runs checks and reports on environment configuration.
"""

from __future__ import annotations

import sys
from argparse import Namespace

from warpdatasets.config import get_settings
from warpdatasets.tools.doctor import (
    run_all_checks,
    format_report,
    format_json,
    has_failures,
)


def run(args: Namespace) -> int:
    """Run the doctor command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    # Get dataset ID if provided
    dataset_id = getattr(args, "dataset", None)

    # Load settings
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        return 1

    # Determine if color should be used
    use_color = not args.no_color and sys.stdout.isatty()

    # Determine verbosity
    verbose = args.verbose

    # Determine if performance check should be run
    include_performance = args.performance

    # Run checks
    results = run_all_checks(
        settings=settings,
        dataset_id=dataset_id,
        include_performance=include_performance,
    )

    # Format output
    if args.format == "json":
        output = format_json(results)
    else:
        output = format_report(results, use_color=use_color, verbose=verbose)

    print(output)

    # Return exit code based on results
    if has_failures(results):
        return 1
    return 0
