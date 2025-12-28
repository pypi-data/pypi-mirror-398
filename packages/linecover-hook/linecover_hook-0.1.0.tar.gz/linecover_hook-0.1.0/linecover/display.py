"""Detailed coverage display functions."""

from pathlib import Path

from loguru import logger

from linecover.models import CoverageMetrics, FileMetrics


def show_file_coverage(filepath: str, metrics: CoverageMetrics) -> None:
    """Show detailed line-by-line coverage for a file.

    Uses +/- notation similar to diff output:
    + for covered lines
    - for uncovered lines
      for non-executable lines

    Args:
        filepath: Path to the file
        metrics: Coverage metrics containing line coverage data
    """
    if filepath not in metrics.file_metrics:
        logger.warning(f"No coverage data for {filepath}")
        return

    file_metrics = metrics.file_metrics[filepath]
    covered = set(file_metrics.covered_lines)
    missing = set(file_metrics.missing_lines)

    try:
        path = Path(filepath)
        content = path.read_text()
        lines = content.splitlines()

        print(f"\n{'=' * 80}")
        print(f"File: {filepath}")
        print(
            f"Coverage: {file_metrics.line_coverage:.1f}% "
            f"({file_metrics.executed_lines}/{file_metrics.total_lines} lines)"
        )
        print(f"{'=' * 80}")

        for line_num, line_content in enumerate(lines, start=1):
            if line_num in covered:
                prefix = "+"
            elif line_num in missing:
                prefix = "-"
            else:
                prefix = " "
            print(f"{prefix} {line_num:4d} | {line_content}")

        print(f"{'=' * 80}\n")

    except Exception as e:
        logger.error(f"Failed to show coverage for {filepath}: {e}")


def show_file_units(filepath: str, file_metrics: FileMetrics, max_units: int) -> None:
    """Show detailed unit information for files exceeding max units.

    Args:
        filepath: Path to the file
        file_metrics: File metrics containing unit details
        max_units: Maximum allowed units
    """
    print(f"\n{'=' * 80}")
    print(f"File: {filepath}")
    print(
        f"Units: {file_metrics.total_units} "
        f"({file_metrics.num_functions} functions, {file_metrics.num_classes} classes)"
    )
    print(f"Exceeds maximum: {max_units}")
    print(f"{'=' * 80}")

    for name, unit_type, line_num in file_metrics.unit_details:
        if unit_type == "class":
            print(f"  Line {line_num:4d}: class {name}")
        else:
            print(f"  Line {line_num:4d}: def {name}")

    print(f"{'=' * 80}\n")
