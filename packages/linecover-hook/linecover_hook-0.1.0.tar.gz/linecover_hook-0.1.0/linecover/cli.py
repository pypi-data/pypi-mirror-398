"""Command-line interface for linecover."""

import sys

import click
from loguru import logger

from linecover.checker import check_violations
from linecover.parser import parse_coverage
from linecover.reporter import report_violations
from linecover.runner import run_pytest as execute_pytest


@click.command(context_settings={"show_default": True})
@click.option(
    "--run-pytest",
    is_flag=True,
    help="Run pytest with coverage before analyzing",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed line-by-line coverage for files below threshold",
)
@click.option(
    "--ignore-dir",
    multiple=True,
    default=["tests/"],
    show_default=True,
    help="Directories to ignore (can be specified multiple times)",
)
@click.option(
    "--line-threshold",
    type=float,
    default=90.0,
    show_default=True,
    help="Minimum line coverage percentage per file",
)
@click.option(
    "--func-threshold",
    type=float,
    default=90.0,
    show_default=True,
    help="Minimum function/class coverage percentage",
)
@click.option(
    "--total-threshold",
    type=float,
    default=90.0,
    show_default=True,
    help="Minimum total project coverage percentage",
)
@click.option(
    "--max-units",
    type=int,
    default=2,
    show_default=True,
    help="Maximum number of functions/classes per file",
)
@click.option(
    "--max-lines",
    type=int,
    default=600,
    show_default=True,
    help="Maximum lines per file",
)
@click.option(
    "--logfile",
    type=click.Path(),
    default=None,
    help="Write logs to file",
)
@click.option(
    "--loglevel",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set log level",
)
def main(
    run_pytest: bool,
    verbose: bool,
    ignore_dir: tuple[str, ...],
    line_threshold: float,
    func_threshold: float,
    total_threshold: float,
    max_units: int,
    max_lines: int,
    logfile: str | None,
    loglevel: str,
) -> None:
    """LineCover - Code coverage enforcement tool.

    Analyzes pytest coverage reports and enforces code quality standards.
    Reports violations in flake8-compatible format.
    """
    # Configure logging
    logger.remove()  # Remove default handler

    # Add stderr handler with level
    logger.add(sys.stderr, level=loglevel.upper())

    # Add file handler if specified
    if logfile:
        logger.add(logfile, level=loglevel.upper())

    logger.info("LineCover starting...")
    logger.debug(
        f"Configuration: line={line_threshold}, func={func_threshold}, "
        f"total={total_threshold}, max_units={max_units}, max_lines={max_lines}"
    )

    # Run pytest if requested
    if run_pytest:
        success = execute_pytest()
        if not success:
            logger.error("Failed to run pytest")
            sys.exit(1)

    # Parse coverage data
    try:
        metrics = parse_coverage(ignore_dirs=list(ignore_dir))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to parse coverage: {e}")
        sys.exit(1)

    # Check for violations
    violations = check_violations(
        metrics,
        line_threshold=line_threshold,
        func_threshold=func_threshold,
        total_threshold=total_threshold,
        max_units=max_units,
        max_lines=max_lines,
    )

    # Report violations
    report_violations(violations, metrics=metrics, verbose=verbose, max_units=max_units)

    # Exit with error code if violations found
    if violations:
        logger.error(f"Found {len(violations)} violation(s)")
        sys.exit(1)
    else:
        logger.success("No violations found!")
        sys.exit(0)


if __name__ == "__main__":
    main()
