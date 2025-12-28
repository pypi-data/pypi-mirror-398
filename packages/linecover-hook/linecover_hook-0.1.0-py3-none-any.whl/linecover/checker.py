"""Violation checker for coverage and complexity thresholds."""

from loguru import logger

from linecover.models import CoverageMetrics, FileMetrics
from linecover.violations import Violation


def check_violations(
    metrics: CoverageMetrics,
    line_threshold: float | None = None,
    func_threshold: float | None = None,
    total_threshold: float | None = None,
    max_units: int | None = None,
    max_lines: int | None = None,
) -> list[Violation]:
    """Check for violations against thresholds.

    Args:
        metrics: Coverage metrics from parser
        line_threshold: Minimum line coverage percentage per file
        func_threshold: Minimum function/class coverage percentage
        total_threshold: Minimum total project coverage percentage
        max_units: Maximum number of functions/classes per file
        max_lines: Maximum lines per file

    Returns:
        List of violations found
    """
    violations: list[Violation] = []

    # Check total project coverage
    if total_threshold is not None and metrics.total_coverage < total_threshold:
        violation = Violation(
            filepath="<total>",
            line=1,
            column=1,
            code="COV001",
            message=(
                f"Total project coverage {metrics.total_coverage:.1f}% "
                f"is below threshold {total_threshold:.1f}%"
            ),
        )
        violations.append(violation)
        logger.warning(f"Total coverage violation: {violation.message}")

    # Check per-file violations
    for filepath, file_metrics in metrics.file_metrics.items():
        # Check line coverage
        if line_threshold is not None and file_metrics.line_coverage < line_threshold:
            violation = Violation(
                filepath=filepath,
                line=1,
                column=1,
                code="COV001",
                message=(
                    f"Line coverage {file_metrics.line_coverage:.1f}% "
                    f"is below threshold {line_threshold:.1f}%"
                ),
            )
            violations.append(violation)
            logger.debug(f"{filepath}: {violation.message}")

        # Check function/class coverage (based on missing lines)
        if func_threshold is not None:
            func_cov = _calculate_function_coverage(file_metrics)
            if func_cov < func_threshold:
                violation = Violation(
                    filepath=filepath,
                    line=1,
                    column=1,
                    code="COV002",
                    message=(
                        f"Function coverage {func_cov:.1f}% "
                        f"is below threshold {func_threshold:.1f}%"
                    ),
                )
                violations.append(violation)
                logger.debug(f"{filepath}: {violation.message}")

        # Check max units (functions + classes)
        if max_units is not None and file_metrics.total_units > max_units:
            violation = Violation(
                filepath=filepath,
                line=1,
                column=1,
                code="COV003",
                message=(
                    f"File has {file_metrics.total_units} units "
                    f"(functions+classes), exceeds maximum {max_units}"
                ),
            )
            violations.append(violation)
            logger.debug(f"{filepath}: {violation.message}")

        # Check max lines
        if max_lines is not None and file_metrics.num_code_lines > max_lines:
            violation = Violation(
                filepath=filepath,
                line=1,
                column=1,
                code="COV004",
                message=(
                    f"File has {file_metrics.num_code_lines} lines, "
                    f"exceeds maximum {max_lines}"
                ),
            )
            violations.append(violation)
            logger.debug(f"{filepath}: {violation.message}")

    logger.info(f"Found {len(violations)} violation(s)")
    return violations


def _calculate_function_coverage(file_metrics: FileMetrics) -> float:
    """Calculate function/class coverage percentage.

    This is a simplified calculation based on line coverage.
    A more accurate implementation would require AST analysis
    to determine which specific functions/classes are covered.

    Args:
        file_metrics: File metrics

    Returns:
        Function coverage percentage (0-100)
    """
    # For now, use line coverage as a proxy for function coverage
    # In a real implementation, we'd parse the AST and check which
    # functions/classes have at least one covered line
    return file_metrics.line_coverage
