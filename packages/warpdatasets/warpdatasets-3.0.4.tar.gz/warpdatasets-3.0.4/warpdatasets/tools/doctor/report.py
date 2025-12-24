"""Report formatting for doctor checks.

Formats CheckResults into human-readable reports.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from warpdatasets.tools.doctor.checks import CheckResult, CheckStatus

if TYPE_CHECKING:
    pass


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    GRAY = "\033[90m"
    CYAN = "\033[36m"


def _status_symbol(status: CheckStatus, use_color: bool = True) -> str:
    """Get a symbol for a check status.

    Args:
        status: Check status
        use_color: Whether to use ANSI colors

    Returns:
        Status symbol
    """
    if status == CheckStatus.PASS:
        symbol = "✓"
        color = Colors.GREEN
    elif status == CheckStatus.FAIL:
        symbol = "✗"
        color = Colors.RED
    elif status == CheckStatus.WARN:
        symbol = "!"
        color = Colors.YELLOW
    else:  # SKIP
        symbol = "-"
        color = Colors.GRAY

    if use_color:
        return f"{color}{symbol}{Colors.RESET}"
    return symbol


def _status_text(status: CheckStatus) -> str:
    """Get text representation of status.

    Args:
        status: Check status

    Returns:
        Status text
    """
    return status.value.upper()


def format_result(result: CheckResult, use_color: bool = True, verbose: bool = False) -> str:
    """Format a single check result.

    Args:
        result: Check result to format
        use_color: Whether to use ANSI colors
        verbose: Whether to include extra details

    Returns:
        Formatted string
    """
    lines = []

    # Main line
    symbol = _status_symbol(result.status, use_color)
    lines.append(f"{symbol} {result.name}: {result.message}")

    # Details (in verbose mode or for failures)
    if result.details and (verbose or result.status == CheckStatus.FAIL):
        lines.append(f"    {result.details}")

    # Suggestion for failures and warnings
    if result.suggestion and result.status in (CheckStatus.FAIL, CheckStatus.WARN):
        if use_color:
            lines.append(f"    {Colors.CYAN}→ {result.suggestion}{Colors.RESET}")
        else:
            lines.append(f"    → {result.suggestion}")

    return "\n".join(lines)


def format_report(
    results: list[CheckResult],
    use_color: bool = True,
    verbose: bool = False,
) -> str:
    """Format a full doctor report.

    Args:
        results: List of check results
        use_color: Whether to use ANSI colors
        verbose: Whether to include extra details

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    if use_color:
        lines.append(f"{Colors.BOLD}warpdatasets doctor{Colors.RESET}")
    else:
        lines.append("warpdatasets doctor")
    lines.append("")

    # Results
    for result in results:
        lines.append(format_result(result, use_color, verbose))

    # Summary
    lines.append("")
    passed = sum(1 for r in results if r.status == CheckStatus.PASS)
    failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
    warned = sum(1 for r in results if r.status == CheckStatus.WARN)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIP)

    summary_parts = []
    if passed:
        if use_color:
            summary_parts.append(f"{Colors.GREEN}{passed} passed{Colors.RESET}")
        else:
            summary_parts.append(f"{passed} passed")
    if failed:
        if use_color:
            summary_parts.append(f"{Colors.RED}{failed} failed{Colors.RESET}")
        else:
            summary_parts.append(f"{failed} failed")
    if warned:
        if use_color:
            summary_parts.append(f"{Colors.YELLOW}{warned} warnings{Colors.RESET}")
        else:
            summary_parts.append(f"{warned} warnings")
    if skipped:
        if use_color:
            summary_parts.append(f"{Colors.GRAY}{skipped} skipped{Colors.RESET}")
        else:
            summary_parts.append(f"{skipped} skipped")

    lines.append(", ".join(summary_parts))

    return "\n".join(lines)


def format_json(results: list[CheckResult]) -> str:
    """Format results as JSON.

    Args:
        results: List of check results

    Returns:
        JSON string
    """
    data = {
        "results": [
            {
                "name": r.name,
                "status": r.status.value,
                "message": r.message,
                "details": r.details,
                "suggestion": r.suggestion,
            }
            for r in results
        ],
        "summary": {
            "passed": sum(1 for r in results if r.status == CheckStatus.PASS),
            "failed": sum(1 for r in results if r.status == CheckStatus.FAIL),
            "warned": sum(1 for r in results if r.status == CheckStatus.WARN),
            "skipped": sum(1 for r in results if r.status == CheckStatus.SKIP),
        },
    }
    return json.dumps(data, indent=2)


def has_failures(results: list[CheckResult]) -> bool:
    """Check if any results are failures.

    Args:
        results: List of check results

    Returns:
        True if any check failed
    """
    return any(r.status == CheckStatus.FAIL for r in results)
