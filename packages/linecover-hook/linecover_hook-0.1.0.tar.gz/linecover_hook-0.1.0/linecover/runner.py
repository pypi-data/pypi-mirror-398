"""Pytest runner for executing tests with coverage."""

import subprocess
from pathlib import Path

from loguru import logger


def run_pytest() -> bool:
    """Run pytest with coverage.

    Returns:
        True if pytest ran successfully, False otherwise
    """
    # Delete old coverage file if it exists
    coverage_file = Path(".coverage")
    if coverage_file.exists():
        logger.debug("Removing existing .coverage file")
        coverage_file.unlink()

    logger.info("Running pytest with coverage...")

    try:
        result = subprocess.run(
            ["pytest", "--cov", "--cov-report="],
            capture_output=True,
            text=True,
            check=False,
        )

        # Log pytest output
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.debug(f"pytest: {line}")

        if result.stderr:
            for line in result.stderr.splitlines():
                logger.warning(f"pytest stderr: {line}")

        if result.returncode == 0:
            logger.info("Pytest completed successfully")
            return True
        else:
            logger.warning(f"Pytest exited with code {result.returncode}")
            return True  # Still return True as we want to analyze coverage even if tests fail

    except FileNotFoundError:
        logger.error("pytest command not found. Is pytest installed?")
        return False
    except Exception as e:
        logger.error(f"Failed to run pytest: {e}")
        return False
