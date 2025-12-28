"""Data models for coverage metrics."""

from dataclasses import dataclass


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    filepath: str
    line_coverage: float
    executed_lines: int
    total_lines: int
    missing_lines: list[int]
    covered_lines: list[int]
    num_functions: int
    num_classes: int
    total_units: int
    num_code_lines: int
    unit_details: list[tuple[str, str, int]]  # [(name, type, line), ...]


@dataclass
class CoverageMetrics:
    """Overall coverage metrics."""

    file_metrics: dict[str, FileMetrics]
    total_coverage: float
    total_executed: int
    total_statements: int
