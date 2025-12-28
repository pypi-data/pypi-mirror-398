"""Coverage parser for extracting metrics from coverage.py data."""

import ast
from pathlib import Path

from coverage import Coverage
from loguru import logger

from linecover.models import CoverageMetrics, FileMetrics


def count_units_and_lines(
    filepath: str,
) -> tuple[int, int, int, list[tuple[str, str, int]]]:
    """Count functions, classes, and lines in a Python file using AST.

    Args:
        filepath: Path to Python file

    Returns:
        Tuple of (num_functions, num_classes, num_code_lines, unit_details)
        where unit_details is [(name, type, line_number), ...]
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=filepath)

        functions = 0
        classes = 0
        unit_details = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                functions += 1
                unit_type = "function"
                unit_details.append((node.name, unit_type, node.lineno))
            elif isinstance(node, ast.ClassDef):
                classes += 1
                unit_type = "class"
                unit_details.append((node.name, unit_type, node.lineno))

        # Count non-empty lines
        num_lines = sum(1 for line in source.splitlines() if line.strip())

        # Sort unit_details by line number
        unit_details.sort(key=lambda x: x[2])

        return functions, classes, num_lines, unit_details

    except (OSError, SyntaxError) as e:
        logger.warning(f"Failed to parse {filepath}: {e}")
        return 0, 0, 0, []


def parse_coverage(ignore_dirs: list[str] | None = None) -> CoverageMetrics:
    """Parse coverage data from .coverage file.

    Args:
        ignore_dirs: List of directory patterns to ignore (default: ["tests/"])

    Returns:
        CoverageMetrics object with all metrics

    Raises:
        FileNotFoundError: If .coverage file doesn't exist
        Exception: If coverage data cannot be loaded
    """
    if ignore_dirs is None:
        ignore_dirs = ["tests/"]

    coverage_file = Path(".coverage")
    if not coverage_file.exists():
        msg = "No .coverage file found. Run pytest with --cov first."
        raise FileNotFoundError(msg)

    try:
        cov = Coverage()
        cov.load()
    except Exception as e:
        msg = f"Failed to load coverage data: {e}"
        raise Exception(msg) from e

    file_metrics = {}
    total_executed = 0
    total_statements = 0

    # Get all measured files
    measured_files = cov.get_data().measured_files()

    for filepath in measured_files:
        # Skip files outside the project, in site-packages, or in ignored directories
        path = Path(filepath)
        path_str = str(path)

        # Check if file should be ignored
        should_ignore = not path.exists() or "site-packages" in path_str
        if not should_ignore:
            for ignore_dir in ignore_dirs:
                if f"/{ignore_dir}" in path_str or path_str.startswith(ignore_dir):
                    should_ignore = True
                    break

        if should_ignore:
            continue

        try:
            # Get coverage analysis for this file
            analysis = cov.analysis2(filepath)
            # analysis2 returns: (filename, executed, excluded, missing, formatted)
            # or (filename, executed, excluded, missing) in older versions
            if len(analysis) == 5:
                _, executed, _, missing, _ = analysis
            else:
                _, executed, _, missing = analysis

            num_executed = len(executed)
            num_missing = len(missing)
            num_statements = num_executed + num_missing

            if num_statements == 0:
                line_coverage_pct = 100.0
            else:
                line_coverage_pct = (num_executed / num_statements) * 100

            # Count functions and classes
            num_funcs, num_classes, num_lines, unit_details = count_units_and_lines(
                filepath
            )

            metrics = FileMetrics(
                filepath=str(path),
                line_coverage=line_coverage_pct,
                executed_lines=num_executed,
                total_lines=num_statements,
                missing_lines=sorted(missing),
                covered_lines=sorted(executed),
                num_functions=num_funcs,
                num_classes=num_classes,
                total_units=num_funcs + num_classes,
                num_code_lines=num_lines,
                unit_details=unit_details,
            )

            file_metrics[str(path)] = metrics
            total_executed += num_executed
            total_statements += num_statements

            logger.debug(
                f"{filepath}: {line_coverage_pct:.1f}% "
                f"({num_executed}/{num_statements} lines, "
                f"{num_funcs} funcs, {num_classes} classes)"
            )

        except Exception as e:
            logger.warning(f"Failed to analyze {filepath}: {e}")
            continue

    # Calculate total coverage
    if total_statements == 0:
        total_coverage = 100.0
    else:
        total_coverage = (total_executed / total_statements) * 100

    logger.info(
        f"Total coverage: {total_coverage:.1f}% "
        f"({total_executed}/{total_statements} lines)"
    )

    return CoverageMetrics(
        file_metrics=file_metrics,
        total_coverage=total_coverage,
        total_executed=total_executed,
        total_statements=total_statements,
    )
