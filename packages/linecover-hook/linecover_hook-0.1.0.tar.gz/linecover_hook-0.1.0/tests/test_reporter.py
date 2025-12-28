"""Tests for flake8-style reporter."""

from io import StringIO
from unittest.mock import patch

from linecover.violations import Violation
from linecover.reporter import format_violation, report_violations


def test_format_violation_line_coverage() -> None:
    """Test formatting a line coverage violation."""
    violation = Violation(
        filepath="test.py",
        line=1,
        column=1,
        code="COV001",
        message="Line coverage 75.0% is below threshold 90.0%",
    )

    formatted = format_violation(violation)
    assert (
        formatted == "test.py:1:1: COV001 Line coverage 75.0% is below threshold 90.0%"
    )


def test_format_violation_function_coverage() -> None:
    """Test formatting a function coverage violation."""
    violation = Violation(
        filepath="module/file.py",
        line=1,
        column=1,
        code="COV002",
        message="Function coverage 60.0% is below threshold 85.0%",
    )

    formatted = format_violation(violation)
    assert (
        formatted
        == "module/file.py:1:1: COV002 Function coverage 60.0% is below threshold 85.0%"
    )


def test_format_violation_max_units() -> None:
    """Test formatting a max units violation."""
    violation = Violation(
        filepath="complex.py",
        line=1,
        column=1,
        code="COV003",
        message="File has 15 units (functions+classes), exceeds maximum 10",
    )

    formatted = format_violation(violation)
    assert (
        formatted
        == "complex.py:1:1: COV003 File has 15 units (functions+classes), exceeds maximum 10"
    )


def test_format_violation_max_lines() -> None:
    """Test formatting a max lines violation."""
    violation = Violation(
        filepath="long_file.py",
        line=1,
        column=1,
        code="COV004",
        message="File has 650 lines, exceeds maximum 600",
    )

    formatted = format_violation(violation)
    assert (
        formatted == "long_file.py:1:1: COV004 File has 650 lines, exceeds maximum 600"
    )


def test_format_violation_total_coverage() -> None:
    """Test formatting a total coverage violation."""
    violation = Violation(
        filepath="<total>",
        line=1,
        column=1,
        code="COV001",
        message="Total project coverage 70.0% is below threshold 90.0%",
    )

    formatted = format_violation(violation)
    assert (
        formatted
        == "<total>:1:1: COV001 Total project coverage 70.0% is below threshold 90.0%"
    )


def test_report_violations_empty() -> None:
    """Test reporting with no violations."""
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations([])
        output = mock_stdout.getvalue()
        assert output == ""


def test_report_violations_single() -> None:
    """Test reporting a single violation."""
    violation = Violation(
        filepath="test.py",
        line=1,
        column=1,
        code="COV001",
        message="Line coverage 75.0% is below threshold 90.0%",
    )

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations([violation])
        output = mock_stdout.getvalue()
        assert "test.py:1:1: COV001" in output
        assert "Line coverage 75.0%" in output


def test_report_violations_multiple() -> None:
    """Test reporting multiple violations."""
    violations = [
        Violation(
            filepath="file1.py",
            line=1,
            column=1,
            code="COV001",
            message="Line coverage 75.0% is below threshold 90.0%",
        ),
        Violation(
            filepath="file2.py",
            line=1,
            column=1,
            code="COV002",
            message="Function coverage 60.0% is below threshold 85.0%",
        ),
        Violation(
            filepath="file3.py",
            line=1,
            column=1,
            code="COV003",
            message="File has 15 units, exceeds maximum 10",
        ),
    ]

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations(violations)
        output = mock_stdout.getvalue()

        assert "file1.py:1:1: COV001" in output
        assert "file2.py:1:1: COV002" in output
        assert "file3.py:1:1: COV003" in output
        assert output.count("\n") == 3  # Three violations


def test_report_violations_preserves_order() -> None:
    """Test that violations are reported in order."""
    violations = [
        Violation(filepath="a.py", line=1, column=1, code="COV001", message="First"),
        Violation(filepath="b.py", line=1, column=1, code="COV002", message="Second"),
        Violation(filepath="c.py", line=1, column=1, code="COV003", message="Third"),
    ]

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations(violations)
        output = mock_stdout.getvalue()
        lines = output.strip().split("\n")

        assert len(lines) == 3
        assert "a.py:1:1: COV001 First" in lines[0]
        assert "b.py:1:1: COV002 Second" in lines[1]
        assert "c.py:1:1: COV003 Third" in lines[2]


def test_report_violations_verbose_hint() -> None:
    """Test that hint about --verbose is shown when there are coverage violations."""
    from linecover.models import CoverageMetrics, FileMetrics

    violations = [
        Violation(
            filepath="test.py",
            line=1,
            column=1,
            code="COV001",
            message="Line coverage 75.0% is below threshold 90.0%",
        )
    ]

    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=75.0,
        executed_lines=15,
        total_lines=20,
        missing_lines=[1, 2, 3, 4, 5],
        covered_lines=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        num_functions=2,
        num_classes=0,
        total_units=2,
        num_code_lines=25,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=75.0,
        total_executed=15,
        total_statements=20,
    )

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations(violations, metrics=metrics, verbose=False)
        output = mock_stdout.getvalue()

        assert "Hint: Use --verbose" in output
        assert "DETAILED COVERAGE REPORT" not in output


def test_report_violations_verbose_output(tmp_path) -> None:
    """Test that verbose mode shows detailed coverage."""
    from linecover.models import CoverageMetrics, FileMetrics

    # Create a temp file
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """def foo():
    return 1

def bar():
    return 2
"""
    )

    violations = [
        Violation(
            filepath=str(test_file),
            line=1,
            column=1,
            code="COV001",
            message="Line coverage 50.0% is below threshold 90.0%",
        )
    ]

    file_metrics = FileMetrics(
        filepath=str(test_file),
        line_coverage=50.0,
        executed_lines=2,
        total_lines=4,
        missing_lines=[1, 4],
        covered_lines=[2, 5],
        num_functions=2,
        num_classes=0,
        total_units=2,
        num_code_lines=5,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={str(test_file): file_metrics},
        total_coverage=50.0,
        total_executed=2,
        total_statements=4,
    )

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations(violations, metrics=metrics, verbose=True)
        output = mock_stdout.getvalue()

        assert "DETAILED COVERAGE REPORT" in output
        assert str(test_file) in output
        assert "+ " in output  # Covered lines
        assert "- " in output  # Missing lines
        assert "  " in output  # Non-executable lines
        assert "Hint: Use --verbose" not in output


def test_show_file_coverage_missing_file() -> None:
    """Test show_file_coverage with file not in metrics."""
    from linecover.parser import CoverageMetrics

    metrics = CoverageMetrics(
        file_metrics={},
        total_coverage=100.0,
        total_executed=10,
        total_statements=10,
    )

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        from linecover.display import show_file_coverage

        show_file_coverage("missing.py", metrics)
        # Should just log a warning, not crash


def test_report_violations_verbose_cov003(tmp_path) -> None:
    """Test that verbose mode shows detailed unit information for COV003 violations."""
    from linecover.models import CoverageMetrics, FileMetrics

    # Create a temp file with multiple units
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class FirstClass:
    pass

def first_func():
    return 1

class SecondClass:
    pass

def second_func():
    return 2
"""
    )

    violations = [
        Violation(
            filepath=str(test_file),
            line=1,
            column=1,
            code="COV003",
            message="File has 4 units (functions+classes), exceeds maximum 2",
        )
    ]

    file_metrics = FileMetrics(
        filepath=str(test_file),
        line_coverage=100.0,
        executed_lines=10,
        total_lines=10,
        missing_lines=[],
        covered_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        num_functions=2,
        num_classes=2,
        total_units=4,
        num_code_lines=10,
        unit_details=[
            ("FirstClass", "class", 1),
            ("first_func", "function", 4),
            ("SecondClass", "class", 7),
            ("second_func", "function", 10),
        ],
    )

    metrics = CoverageMetrics(
        file_metrics={str(test_file): file_metrics},
        total_coverage=100.0,
        total_executed=10,
        total_statements=10,
    )

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations(violations, metrics=metrics, verbose=True, max_units=2)
        output = mock_stdout.getvalue()

        assert "DETAILED MAX-UNITS VIOLATIONS" in output
        assert str(test_file) in output
        assert "class FirstClass" in output
        assert "def first_func" in output
        assert "class SecondClass" in output
        assert "def second_func" in output
        assert "Exceeds maximum: 2" in output


def test_report_violations_cov003_hint() -> None:
    """Test that hint about --verbose is shown for COV003 violations."""
    from linecover.models import CoverageMetrics, FileMetrics

    violations = [
        Violation(
            filepath="test.py",
            line=1,
            column=1,
            code="COV003",
            message="File has 4 units, exceeds maximum 2",
        )
    ]

    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=100.0,
        executed_lines=10,
        total_lines=10,
        missing_lines=[],
        covered_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        num_functions=2,
        num_classes=2,
        total_units=4,
        num_code_lines=10,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=100.0,
        total_executed=10,
        total_statements=10,
    )

    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        report_violations(violations, metrics=metrics, verbose=False, max_units=2)
        output = mock_stdout.getvalue()

        assert "Hint: Use --verbose" in output
        assert "max-units violations" in output
        assert "DETAILED MAX-UNITS VIOLATIONS" not in output
