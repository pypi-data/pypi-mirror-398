"""Tests for coverage parser."""

import tempfile
from pathlib import Path

import pytest
from coverage import Coverage

from linecover.parser import (
    CoverageMetrics,
    FileMetrics,
    count_units_and_lines,
    parse_coverage,
)


def test_count_units_simple_file() -> None:
    """Test counting functions and classes in a simple file."""
    code = """
def foo():
    pass

def bar():
    pass

class MyClass:
    def method(self):
        pass
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        filepath = f.name

    try:
        funcs, classes, lines, _ = count_units_and_lines(filepath)
        assert funcs == 3  # foo, bar, method
        assert classes == 1  # MyClass
        assert lines > 0
    finally:
        Path(filepath).unlink()


def test_count_units_async_functions() -> None:
    """Test counting async functions."""
    code = """
async def async_foo():
    pass

class MyClass:
    async def async_method(self):
        pass
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        filepath = f.name

    try:
        funcs, classes, lines, _ = count_units_and_lines(filepath)
        assert funcs == 2  # async_foo, async_method
        assert classes == 1  # MyClass
    finally:
        Path(filepath).unlink()


def test_count_units_empty_file() -> None:
    """Test counting in empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        filepath = f.name

    try:
        funcs, classes, lines, _ = count_units_and_lines(filepath)
        assert funcs == 0
        assert classes == 0
        assert lines == 0
    finally:
        Path(filepath).unlink()


def test_count_units_invalid_syntax() -> None:
    """Test handling of invalid Python syntax."""
    code = "def foo( invalid syntax"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        filepath = f.name

    try:
        funcs, classes, lines, _ = count_units_and_lines(filepath)
        assert funcs == 0
        assert classes == 0
        assert lines == 0
    finally:
        Path(filepath).unlink()


def test_count_units_nonexistent_file() -> None:
    """Test handling of nonexistent file."""
    funcs, classes, lines, _ = count_units_and_lines("/nonexistent/file.py")
    assert funcs == 0
    assert classes == 0
    assert lines == 0


def test_count_units_extracts_details() -> None:
    """Test that count_units_and_lines extracts unit details correctly."""
    code = """
class MyClass:
    def method(self):
        pass

def standalone_func():
    return 42

class AnotherClass:
    pass
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        filepath = f.name

    try:
        funcs, classes, lines, unit_details = count_units_and_lines(filepath)

        # Check counts
        assert funcs == 2  # method and standalone_func
        assert classes == 2  # MyClass and AnotherClass

        # Check unit_details format
        assert len(unit_details) == 4
        assert all(len(detail) == 3 for detail in unit_details)

        # Check unit details are sorted by line number
        assert unit_details[0][0] == "MyClass"
        assert unit_details[0][1] == "class"
        assert unit_details[1][0] == "method"
        assert unit_details[1][1] == "function"
        assert unit_details[2][0] == "standalone_func"
        assert unit_details[2][1] == "function"
        assert unit_details[3][0] == "AnotherClass"
        assert unit_details[3][1] == "class"

    finally:
        Path(filepath).unlink()


def test_parse_coverage_no_file() -> None:
    """Test parse_coverage when .coverage file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            with pytest.raises(FileNotFoundError, match="No .coverage file found"):
                parse_coverage()
        finally:
            os.chdir(old_cwd)


def test_parse_coverage_with_data() -> None:
    """Test parsing coverage with actual coverage data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        import sys

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create a simple Python file
            test_file = Path("test_module.py")
            test_file.write_text(
                """
def covered():
    return True

def uncovered():
    return False

class TestClass:
    def method(self):
        pass
"""
            )

            # Create coverage data
            cov = Coverage()
            cov.start()

            # Add tmpdir to path and execute only the covered function
            sys.path.insert(0, tmpdir)
            try:
                exec(
                    compile(
                        "from test_module import covered\ncovered()", "<string>", "exec"
                    )
                )  # noqa: S102
            finally:
                sys.path.remove(tmpdir)

            cov.stop()
            cov.save()

            # Parse coverage
            metrics = parse_coverage()

            assert isinstance(metrics, CoverageMetrics)
            assert metrics.total_coverage >= 0
            assert metrics.total_coverage <= 100
            assert len(metrics.file_metrics) > 0

            # Check that our test file is in the metrics
            test_file_str = str(test_file.absolute())
            if test_file_str in metrics.file_metrics:
                file_metric = metrics.file_metrics[test_file_str]
                assert isinstance(file_metric, FileMetrics)
                assert file_metric.num_functions > 0
                assert file_metric.num_classes >= 0

        finally:
            os.chdir(old_cwd)


def test_file_metrics_dataclass() -> None:
    """Test FileMetrics dataclass."""
    metrics = FileMetrics(
        filepath="test.py",
        line_coverage=85.5,
        executed_lines=17,
        total_lines=20,
        missing_lines=[5, 10, 15],
        covered_lines=[],
        num_functions=3,
        num_classes=1,
        total_units=4,
        num_code_lines=25,
        unit_details=[],
    )

    assert metrics.filepath == "test.py"
    assert metrics.line_coverage == 85.5
    assert metrics.executed_lines == 17
    assert metrics.total_lines == 20
    assert metrics.missing_lines == [5, 10, 15]
    assert metrics.num_functions == 3
    assert metrics.num_classes == 1
    assert metrics.total_units == 4
    assert metrics.num_code_lines == 25


def test_coverage_metrics_dataclass() -> None:
    """Test CoverageMetrics dataclass."""
    file_metric = FileMetrics(
        filepath="test.py",
        line_coverage=90.0,
        executed_lines=18,
        total_lines=20,
        missing_lines=[5, 10],
        covered_lines=[],
        num_functions=2,
        num_classes=1,
        total_units=3,
        num_code_lines=30,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metric},
        total_coverage=90.0,
        total_executed=18,
        total_statements=20,
    )

    assert metrics.total_coverage == 90.0
    assert metrics.total_executed == 18
    assert metrics.total_statements == 20
    assert len(metrics.file_metrics) == 1
    assert "test.py" in metrics.file_metrics


def test_parse_coverage_load_error() -> None:
    """Test handling of coverage load errors."""
    import tempfile
    from unittest.mock import patch, Mock
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Create a .coverage file
            Path(".coverage").write_text("")

            # Mock Coverage to raise an error
            with patch("linecover.parser.Coverage") as mock_cov_class:
                mock_cov = Mock()
                mock_cov.load.side_effect = Exception("Load failed")
                mock_cov_class.return_value = mock_cov

                with pytest.raises(Exception, match="Failed to load coverage data"):
                    parse_coverage()
        finally:
            os.chdir(old_cwd)


def test_parse_coverage_skips_missing_files() -> None:
    """Test that parse_coverage skips files that don't exist."""
    import tempfile
    from unittest.mock import patch, Mock
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create a .coverage file
            Path(".coverage").write_text("")

            # Mock Coverage to return a non-existent file
            with patch("linecover.parser.Coverage") as mock_cov_class:
                mock_cov = Mock()
                mock_data = Mock()
                mock_data.measured_files.return_value = ["/nonexistent/file.py"]
                mock_cov.get_data.return_value = mock_data
                mock_cov_class.return_value = mock_cov

                metrics = parse_coverage()
                # Should have no file metrics since file doesn't exist
                assert len(metrics.file_metrics) == 0
                assert metrics.total_coverage == 100.0  # No statements means 100%
        finally:
            os.chdir(old_cwd)


def test_parse_coverage_handles_analysis_errors() -> None:
    """Test that parse_coverage handles analysis errors gracefully."""
    import tempfile
    from unittest.mock import patch, Mock
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create a test file
            test_file = Path("test.py")
            test_file.write_text("def foo(): pass")

            # Create a .coverage file
            Path(".coverage").write_text("")

            # Mock Coverage to raise an error during analysis
            with patch("linecover.parser.Coverage") as mock_cov_class:
                mock_cov = Mock()
                mock_data = Mock()
                mock_data.measured_files.return_value = [str(test_file.absolute())]
                mock_cov.get_data.return_value = mock_data
                mock_cov.analysis2.side_effect = Exception("Analysis failed")
                mock_cov_class.return_value = mock_cov

                metrics = parse_coverage()
                # Should skip the file that failed analysis
                assert len(metrics.file_metrics) == 0
        finally:
            os.chdir(old_cwd)


def test_parse_coverage_with_old_api() -> None:
    """Test parse_coverage handles old coverage.py API (4 values)."""
    import tempfile
    from unittest.mock import patch, Mock
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create a test file
            test_file = Path("test.py")
            test_file.write_text("def foo():\n    return 1\n")

            # Create a .coverage file
            Path(".coverage").write_text("")

            # Mock Coverage to return old API format (4 values)
            with patch("linecover.parser.Coverage") as mock_cov_class:
                mock_cov = Mock()
                mock_data = Mock()
                mock_data.measured_files.return_value = [str(test_file.absolute())]
                mock_cov.get_data.return_value = mock_data
                # Old API returns 4 values
                mock_cov.analysis2.return_value = (
                    str(test_file.absolute()),
                    [2],  # executed
                    [],  # excluded
                    [1],  # missing
                )
                mock_cov_class.return_value = mock_cov

                metrics = parse_coverage()
                assert len(metrics.file_metrics) == 1
                file_metric = metrics.file_metrics[str(test_file.absolute())]
                assert file_metric.executed_lines == 1
                assert file_metric.total_lines == 2
        finally:
            os.chdir(old_cwd)
