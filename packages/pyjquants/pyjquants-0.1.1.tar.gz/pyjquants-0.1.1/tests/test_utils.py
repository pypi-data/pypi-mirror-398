"""Tests for pyjquants utils."""

from __future__ import annotations

import datetime

import pytest

from pyjquants.utils.date import is_weekend, parse_date, format_date


class TestIsWeekend:
    """Tests for is_weekend function."""

    def test_saturday(self) -> None:
        """Test Saturday is weekend."""
        # 2024-01-13 is Saturday
        assert is_weekend(datetime.date(2024, 1, 13)) is True

    def test_sunday(self) -> None:
        """Test Sunday is weekend."""
        # 2024-01-14 is Sunday
        assert is_weekend(datetime.date(2024, 1, 14)) is True

    def test_weekday(self) -> None:
        """Test weekdays are not weekend."""
        # 2024-01-15 is Monday
        assert is_weekend(datetime.date(2024, 1, 15)) is False
        # 2024-01-16 is Tuesday
        assert is_weekend(datetime.date(2024, 1, 16)) is False
        # 2024-01-17 is Wednesday
        assert is_weekend(datetime.date(2024, 1, 17)) is False
        # 2024-01-18 is Thursday
        assert is_weekend(datetime.date(2024, 1, 18)) is False
        # 2024-01-19 is Friday
        assert is_weekend(datetime.date(2024, 1, 19)) is False


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_date_object(self) -> None:
        """Test parsing date object returns same object."""
        d = datetime.date(2024, 1, 15)
        result = parse_date(d)
        assert result == d

    def test_parse_iso_format(self) -> None:
        """Test parsing YYYY-MM-DD format."""
        result = parse_date("2024-01-15")
        assert result == datetime.date(2024, 1, 15)

    def test_parse_yyyymmdd_format(self) -> None:
        """Test parsing YYYYMMDD format."""
        result = parse_date("20240115")
        assert result == datetime.date(2024, 1, 15)

    def test_parse_none(self) -> None:
        """Test parsing None returns None."""
        result = parse_date(None)
        assert result is None

    def test_parse_invalid_string(self) -> None:
        """Test parsing invalid string returns None."""
        assert parse_date("invalid") is None
        assert parse_date("2024-13-01") is None  # Invalid month
        assert parse_date("1234567") is None  # Wrong length

    def test_parse_invalid_type(self) -> None:
        """Test parsing invalid type returns None."""
        assert parse_date(123) is None
        assert parse_date([2024, 1, 15]) is None


class TestFormatDate:
    """Tests for format_date function."""

    def test_format_yyyymmdd(self) -> None:
        """Test formatting to YYYYMMDD."""
        d = datetime.date(2024, 1, 15)
        result = format_date(d, "yyyymmdd")
        assert result == "20240115"

    def test_format_iso(self) -> None:
        """Test formatting to ISO format."""
        d = datetime.date(2024, 1, 15)
        result = format_date(d, "yyyy-mm-dd")
        assert result == "2024-01-15"

    def test_format_default(self) -> None:
        """Test default format is YYYYMMDD."""
        d = datetime.date(2024, 1, 15)
        result = format_date(d)
        assert result == "20240115"
