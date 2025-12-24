"""Doctor tool for warpdatasets.

Diagnoses environment issues and validates configuration.
"""

from warpdatasets.tools.doctor.checks import (
    CheckResult,
    CheckStatus,
    check_settings,
    check_duckdb,
    check_pyarrow,
    check_connectivity,
    check_credentials,
    check_dataset_access,
    check_streaming_performance,
    run_all_checks,
)
from warpdatasets.tools.doctor.report import (
    format_result,
    format_report,
    format_json,
    has_failures,
)

__all__ = [
    "CheckResult",
    "CheckStatus",
    "check_settings",
    "check_duckdb",
    "check_pyarrow",
    "check_connectivity",
    "check_credentials",
    "check_dataset_access",
    "check_streaming_performance",
    "run_all_checks",
    "format_result",
    "format_report",
    "format_json",
    "has_failures",
]
