"""Violation data model."""

from dataclasses import dataclass


@dataclass
class Violation:
    """Represents a single violation."""

    filepath: str
    line: int
    column: int
    code: str
    message: str
