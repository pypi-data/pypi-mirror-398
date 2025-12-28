"""Flake8-style reporter for violations."""

from loguru import logger

from linecover.display import show_file_coverage, show_file_units
from linecover.models import CoverageMetrics
from linecover.violations import Violation


def format_violation(violation: Violation) -> str:
    """Format a violation in flake8 style.

    Args:
        violation: Violation to format

    Returns:
        Formatted string: "filepath:line:column: CODE message"
    """
    return (
        f"{violation.filepath}:{violation.line}:{violation.column}: "
        f"{violation.code} {violation.message}"
    )


def report_violations(
    violations: list[Violation],
    metrics: CoverageMetrics | None = None,
    verbose: bool = False,
    max_units: int | None = None,
) -> None:
    """Report violations to stdout in flake8 format.

    Args:
        violations: List of violations to report
        metrics: Coverage metrics for detailed reporting
        verbose: If True, show detailed line-by-line coverage for failing files
        max_units: Maximum allowed units (for verbose COV003 reporting)
    """
    if not violations:
        logger.info("No violations found!")
        return

    logger.info(f"Reporting {len(violations)} violation(s):")

    # Track files with coverage violations and max-units violations for verbose output
    files_below_threshold = set()
    files_exceeding_units = set()

    for violation in violations:
        formatted = format_violation(violation)
        print(formatted)
        logger.debug(f"Reported: {formatted}")

        # Track files with coverage violations (COV001 or COV002)
        if violation.code in ("COV001", "COV002") and violation.filepath != "<total>":
            files_below_threshold.add(violation.filepath)

        # Track files with max-units violations (COV003)
        if violation.code == "COV003":
            files_exceeding_units.add(violation.filepath)

    # Show hint about verbose mode if there are violations that can show details
    total_files_with_details = len(files_below_threshold) + len(files_exceeding_units)
    if total_files_with_details > 0 and not verbose and metrics:
        hint_parts = []
        if files_below_threshold:
            hint_parts.append(
                f"{len(files_below_threshold)} file(s) with coverage violations"
            )
        if files_exceeding_units:
            hint_parts.append(
                f"{len(files_exceeding_units)} file(s) with max-units violations"
            )

        hint_msg = " and ".join(hint_parts)
        print(f"\nHint: Use --verbose to see detailed information for {hint_msg}")

    # Show detailed coverage if verbose
    if verbose and metrics:
        if files_below_threshold:
            print("\n" + "=" * 80)
            print("DETAILED COVERAGE REPORT")
            print("=" * 80)
            for filepath in sorted(files_below_threshold):
                show_file_coverage(filepath, metrics)

        # Show detailed unit information for COV003 violations
        if files_exceeding_units and max_units is not None:
            print("\n" + "=" * 80)
            print("DETAILED MAX-UNITS VIOLATIONS")
            print("=" * 80)
            for filepath in sorted(files_exceeding_units):
                if filepath in metrics.file_metrics:
                    show_file_units(filepath, metrics.file_metrics[filepath], max_units)
