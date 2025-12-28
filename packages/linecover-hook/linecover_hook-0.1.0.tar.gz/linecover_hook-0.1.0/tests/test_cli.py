"""Tests for CLI interface."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from linecover.violations import Violation
from linecover.cli import main
from linecover.models import CoverageMetrics, FileMetrics


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_metrics() -> CoverageMetrics:
    """Create mock coverage metrics."""
    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=95.0,
        executed_lines=19,
        total_lines=20,
        missing_lines=[10],
        covered_lines=[],
        num_functions=3,
        num_classes=1,
        total_units=4,
        num_code_lines=50,
        unit_details=[],
    )

    return CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=95.0,
        total_executed=19,
        total_statements=20,
    )


def test_cli_no_violations(runner: CliRunner, mock_metrics: CoverageMetrics) -> None:
    """Test CLI with no violations."""
    with (
        patch("linecover.cli.parse_coverage", return_value=mock_metrics),
        patch("linecover.cli.check_violations", return_value=[]),
    ):
        result = runner.invoke(main, ["--line-threshold", "90"])

        assert result.exit_code == 0


def test_cli_with_violations(runner: CliRunner, mock_metrics: CoverageMetrics) -> None:
    """Test CLI with violations."""
    violations = [
        Violation(
            filepath="test.py",
            line=1,
            column=1,
            code="COV001",
            message="Line coverage 75.0% is below threshold 90.0%",
        )
    ]

    with (
        patch("linecover.cli.parse_coverage", return_value=mock_metrics),
        patch("linecover.cli.check_violations", return_value=violations),
    ):
        result = runner.invoke(main, ["--line-threshold", "90"])

        assert result.exit_code == 1
        assert "COV001" in result.output


def test_cli_run_pytest_flag(runner: CliRunner, mock_metrics: CoverageMetrics) -> None:
    """Test CLI with --run-pytest flag."""
    with (
        patch("linecover.cli.execute_pytest", return_value=True) as mock_run,
        patch("linecover.cli.parse_coverage", return_value=mock_metrics),
        patch("linecover.cli.check_violations", return_value=[]),
    ):
        result = runner.invoke(main, ["--run-pytest", "--line-threshold", "90"])

        assert result.exit_code == 0
        mock_run.assert_called_once()


def test_cli_pytest_failure(runner: CliRunner) -> None:
    """Test CLI when pytest fails to run."""
    with patch("linecover.cli.execute_pytest", return_value=False):
        result = runner.invoke(main, ["--run-pytest"])

        assert result.exit_code == 1


def test_cli_no_coverage_file(runner: CliRunner) -> None:
    """Test CLI when .coverage file is missing."""
    with patch(
        "linecover.cli.parse_coverage",
        side_effect=FileNotFoundError("No .coverage file found"),
    ):
        result = runner.invoke(main, [])

        assert result.exit_code == 1


def test_cli_all_thresholds(runner: CliRunner, mock_metrics: CoverageMetrics) -> None:
    """Test CLI with all threshold options."""
    with (
        patch("linecover.cli.parse_coverage", return_value=mock_metrics),
        patch("linecover.cli.check_violations", return_value=[]) as mock_check,
    ):
        result = runner.invoke(
            main,
            [
                "--line-threshold",
                "90",
                "--func-threshold",
                "85",
                "--total-threshold",
                "88",
                "--max-units",
                "10",
                "--max-lines",
                "500",
            ],
        )

        assert result.exit_code == 0
        mock_check.assert_called_once()
        call_kwargs = mock_check.call_args.kwargs
        assert call_kwargs["line_threshold"] == 90.0
        assert call_kwargs["func_threshold"] == 85.0
        assert call_kwargs["total_threshold"] == 88.0
        assert call_kwargs["max_units"] == 10
        assert call_kwargs["max_lines"] == 500


def test_cli_logfile(
    runner: CliRunner, mock_metrics: CoverageMetrics, tmp_path
) -> None:
    """Test CLI with --logfile option."""
    logfile = tmp_path / "test.log"

    with (
        patch("linecover.cli.parse_coverage", return_value=mock_metrics),
        patch("linecover.cli.check_violations", return_value=[]),
    ):
        result = runner.invoke(main, ["--logfile", str(logfile)])

        assert result.exit_code == 0
        assert logfile.exists()


def test_cli_loglevel(runner: CliRunner, mock_metrics: CoverageMetrics) -> None:
    """Test CLI with different log levels."""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        with (
            patch("linecover.cli.parse_coverage", return_value=mock_metrics),
            patch("linecover.cli.check_violations", return_value=[]),
        ):
            result = runner.invoke(main, ["--loglevel", level])

            assert result.exit_code == 0


def test_cli_parse_error(runner: CliRunner) -> None:
    """Test CLI when coverage parsing fails."""
    with patch(
        "linecover.cli.parse_coverage",
        side_effect=Exception("Parse error"),
    ):
        result = runner.invoke(main, [])

        assert result.exit_code == 1


def test_cli_no_options(runner: CliRunner, mock_metrics: CoverageMetrics) -> None:
    """Test CLI with no threshold options (uses defaults)."""
    with (
        patch("linecover.cli.parse_coverage", return_value=mock_metrics),
        patch("linecover.cli.check_violations", return_value=[]) as mock_check,
    ):
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        # Should call check_violations with default thresholds
        mock_check.assert_called_once()
        call_kwargs = mock_check.call_args.kwargs
        assert call_kwargs["line_threshold"] == 90.0
        assert call_kwargs["func_threshold"] == 90.0
        assert call_kwargs["total_threshold"] == 90.0
        assert call_kwargs["max_units"] == 2
        assert call_kwargs["max_lines"] == 600
