"""Tests for violation checker."""

from linecover.checker import check_violations
from linecover.models import CoverageMetrics, FileMetrics
from linecover.violations import Violation


def test_no_violations() -> None:
    """Test that no violations are found when all thresholds are met."""
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

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=95.0,
        total_executed=19,
        total_statements=20,
    )

    violations = check_violations(
        metrics,
        line_threshold=90.0,
        func_threshold=90.0,
        total_threshold=90.0,
        max_units=10,
        max_lines=100,
    )

    assert len(violations) == 0


def test_line_coverage_violation() -> None:
    """Test detection of line coverage violation."""
    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=75.0,
        executed_lines=15,
        total_lines=20,
        missing_lines=[1, 2, 3, 4, 5],
        covered_lines=[],
        num_functions=2,
        num_classes=0,
        total_units=2,
        num_code_lines=30,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=75.0,
        total_executed=15,
        total_statements=20,
    )

    violations = check_violations(metrics, line_threshold=90.0)

    assert len(violations) == 1
    assert violations[0].filepath == "test.py"
    assert violations[0].code == "COV001"
    assert "75.0%" in violations[0].message
    assert "90.0%" in violations[0].message


def test_function_coverage_violation() -> None:
    """Test detection of function coverage violation."""
    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=60.0,
        executed_lines=12,
        total_lines=20,
        missing_lines=[1, 2, 3, 4, 5, 6, 7, 8],
        covered_lines=[],
        num_functions=5,
        num_classes=1,
        total_units=6,
        num_code_lines=40,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=60.0,
        total_executed=12,
        total_statements=20,
    )

    violations = check_violations(metrics, func_threshold=85.0)

    assert len(violations) == 1
    assert violations[0].filepath == "test.py"
    assert violations[0].code == "COV002"
    assert "60.0%" in violations[0].message
    assert "85.0%" in violations[0].message


def test_total_coverage_violation() -> None:
    """Test detection of total project coverage violation."""
    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=70.0,
        executed_lines=14,
        total_lines=20,
        missing_lines=[1, 2, 3, 4, 5, 6],
        covered_lines=[],
        num_functions=2,
        num_classes=0,
        total_units=2,
        num_code_lines=30,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=70.0,
        total_executed=14,
        total_statements=20,
    )

    violations = check_violations(metrics, total_threshold=90.0)

    assert len(violations) == 1
    assert violations[0].filepath == "<total>"
    assert violations[0].code == "COV001"
    assert "70.0%" in violations[0].message
    assert "90.0%" in violations[0].message


def test_max_units_violation() -> None:
    """Test detection of too many units (functions+classes)."""
    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=95.0,
        executed_lines=19,
        total_lines=20,
        missing_lines=[10],
        covered_lines=[],
        num_functions=8,
        num_classes=4,
        total_units=12,
        num_code_lines=200,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=95.0,
        total_executed=19,
        total_statements=20,
    )

    violations = check_violations(metrics, max_units=10)

    assert len(violations) == 1
    assert violations[0].filepath == "test.py"
    assert violations[0].code == "COV003"
    assert "12 units" in violations[0].message
    assert "10" in violations[0].message


def test_max_lines_violation() -> None:
    """Test detection of file with too many lines."""
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
        num_code_lines=650,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=95.0,
        total_executed=19,
        total_statements=20,
    )

    violations = check_violations(metrics, max_lines=500)

    assert len(violations) == 1
    assert violations[0].filepath == "test.py"
    assert violations[0].code == "COV004"
    assert "650 lines" in violations[0].message
    assert "500" in violations[0].message


def test_multiple_violations_same_file() -> None:
    """Test detection of multiple violations in the same file."""
    file_metrics = FileMetrics(
        filepath="bad_file.py",
        line_coverage=60.0,
        executed_lines=12,
        total_lines=20,
        missing_lines=[1, 2, 3, 4, 5, 6, 7, 8],
        covered_lines=[],
        num_functions=10,
        num_classes=5,
        total_units=15,
        num_code_lines=800,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"bad_file.py": file_metrics},
        total_coverage=60.0,
        total_executed=12,
        total_statements=20,
    )

    violations = check_violations(
        metrics,
        line_threshold=80.0,
        func_threshold=80.0,
        total_threshold=80.0,
        max_units=10,
        max_lines=600,
    )

    # Should have: line coverage, func coverage, total coverage, max units, max lines
    assert len(violations) == 5

    codes = {v.code for v in violations}
    assert "COV001" in codes  # Line and total coverage
    assert "COV002" in codes  # Function coverage
    assert "COV003" in codes  # Max units
    assert "COV004" in codes  # Max lines


def test_multiple_files() -> None:
    """Test checking violations across multiple files."""
    file1 = FileMetrics(
        filepath="good.py",
        line_coverage=95.0,
        executed_lines=19,
        total_lines=20,
        missing_lines=[10],
        covered_lines=[],
        num_functions=2,
        num_classes=1,
        total_units=3,
        num_code_lines=50,
        unit_details=[],
    )

    file2 = FileMetrics(
        filepath="bad.py",
        line_coverage=50.0,
        executed_lines=10,
        total_lines=20,
        missing_lines=list(range(1, 11)),
        covered_lines=[],
        num_functions=2,
        num_classes=0,
        total_units=2,
        num_code_lines=40,
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"good.py": file1, "bad.py": file2},
        total_coverage=72.5,
        total_executed=29,
        total_statements=40,
    )

    violations = check_violations(metrics, line_threshold=80.0)

    # Only bad.py should violate
    assert len(violations) == 1
    assert violations[0].filepath == "bad.py"
    assert violations[0].code == "COV001"


def test_violation_dataclass() -> None:
    """Test Violation dataclass."""
    violation = Violation(
        filepath="test.py",
        line=42,
        column=5,
        code="COV001",
        message="Coverage is low",
    )

    assert violation.filepath == "test.py"
    assert violation.line == 42
    assert violation.column == 5
    assert violation.code == "COV001"
    assert violation.message == "Coverage is low"


def test_no_thresholds() -> None:
    """Test that no violations are found when no thresholds are set."""
    file_metrics = FileMetrics(
        filepath="test.py",
        line_coverage=10.0,  # Very low coverage
        executed_lines=2,
        total_lines=20,
        missing_lines=list(range(3, 21)),
        covered_lines=[],
        num_functions=50,  # Many units
        num_classes=50,
        total_units=100,
        num_code_lines=10000,  # Very long file
        unit_details=[],
    )

    metrics = CoverageMetrics(
        file_metrics={"test.py": file_metrics},
        total_coverage=10.0,
        total_executed=2,
        total_statements=20,
    )

    # No thresholds set
    violations = check_violations(metrics)

    assert len(violations) == 0
