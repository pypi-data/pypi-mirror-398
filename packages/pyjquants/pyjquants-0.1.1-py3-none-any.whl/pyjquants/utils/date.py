"""Date utility functions."""

from __future__ import annotations

from datetime import date
from typing import Any


def is_weekend(d: date) -> bool:
    """Check if a date is a weekend (Saturday or Sunday)."""
    return d.weekday() >= 5


def parse_date(value: Any) -> date | None:
    """
    Parse various date formats to date object.

    Supports:
    - date object
    - "YYYY-MM-DD" string
    - "YYYYMMDD" string

    Args:
        value: Date value to parse

    Returns:
        date object or None if parsing fails
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            if "-" in value:
                return date.fromisoformat(value)
            if len(value) == 8:
                return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
        except (ValueError, IndexError):
            pass
    return None


def format_date(d: date, fmt: str = "yyyymmdd") -> str:
    """
    Format date to string.

    Args:
        d: Date to format
        fmt: Format type ("yyyymmdd" or "yyyy-mm-dd")

    Returns:
        Formatted date string
    """
    if fmt == "yyyymmdd":
        return d.strftime("%Y%m%d")
    return d.isoformat()
