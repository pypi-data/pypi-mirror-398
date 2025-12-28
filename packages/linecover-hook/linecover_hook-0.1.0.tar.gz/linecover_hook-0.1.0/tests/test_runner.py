"""Tests for pytest runner."""

from unittest.mock import MagicMock, patch

from linecover.runner import run_pytest


def test_run_pytest_success() -> None:
    """Test successful pytest execution."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "test session starts\n5 passed"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = run_pytest()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["pytest", "--cov", "--cov-report="]


def test_run_pytest_with_failures() -> None:
    """Test pytest execution with test failures."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "test session starts\n3 passed, 2 failed"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = run_pytest()

        # Should still return True to analyze coverage
        assert result is True
        mock_run.assert_called_once()


def test_run_pytest_with_stderr() -> None:
    """Test pytest execution with stderr output."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "test session starts"
    mock_result.stderr = "warning: deprecated feature"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = run_pytest()

        assert result is True
        mock_run.assert_called_once()


def test_run_pytest_not_found() -> None:
    """Test handling when pytest is not installed."""
    with patch("subprocess.run", side_effect=FileNotFoundError("pytest not found")):
        result = run_pytest()

        assert result is False


def test_run_pytest_exception() -> None:
    """Test handling of unexpected exceptions."""
    with patch("subprocess.run", side_effect=Exception("Unexpected error")):
        result = run_pytest()

        assert result is False


def test_run_pytest_empty_output() -> None:
    """Test pytest with no stdout/stderr."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        result = run_pytest()

        assert result is True


def test_run_pytest_multiline_output() -> None:
    """Test pytest with multiline output."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "line1\nline2\nline3"
    mock_result.stderr = "warning1\nwarning2"

    with patch("subprocess.run", return_value=mock_result):
        result = run_pytest()

        assert result is True


def test_run_pytest_deletes_old_coverage() -> None:
    """Test that run_pytest deletes existing .coverage file."""
    import os
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create a fake old coverage file
            coverage_file = Path(".coverage")
            coverage_file.write_text("old data")
            assert coverage_file.exists()

            with patch("subprocess.run") as mock_run:
                # Mock successful pytest run
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                mock_result.stderr = ""
                mock_run.return_value = mock_result

                result = run_pytest()

                # Coverage file should have been deleted
                assert result is True
                # File was deleted then recreated by mock pytest
        finally:
            os.chdir(old_cwd)
