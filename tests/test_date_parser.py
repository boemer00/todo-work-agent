"""
Unit tests for date parsing utilities.

Tests natural language date parsing, timezone handling, and date formatting.
"""

import pytest
from datetime import datetime, timezone
from freezegun import freeze_time

from utils.date_parser import (
    parse_natural_language_date,
    extract_date_from_task,
    datetime_to_iso,
    format_datetime_for_display,
    is_date_in_past
)


@pytest.mark.unit
class TestDateParser:
    """Test suite for date parsing functions."""

    @freeze_time("2025-01-15 10:00:00")
    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow at 10am'."""
        result = parse_natural_language_date("tomorrow at 10am", timezone="UTC")

        assert result is not None
        assert result.day == 16  # Tomorrow is Jan 16
        assert result.hour == 10
        assert result.minute == 0

    @freeze_time("2025-01-15 10:00:00")  # This is a Wednesday
    def test_parse_next_week(self):
        """Test parsing 'Friday at 2pm' (upcoming Friday)."""
        result = parse_natural_language_date("Friday at 2pm", timezone="UTC")

        assert result is not None
        assert result.hour == 14  # 2pm in 24h format
        assert result.minute == 0
        # Should be Friday Jan 17 (2 days ahead from Wednesday Jan 15)
        assert result.day == 17

    @freeze_time("2025-01-15 10:00:00")
    def test_parse_specific_time(self):
        """Test parsing 'today at 3pm'."""
        result = parse_natural_language_date("today at 3pm", timezone="UTC")

        assert result is not None
        assert result.day == 15
        assert result.hour == 15
        assert result.minute == 0

    @freeze_time("2025-01-15 10:00:00")
    def test_parse_relative_time(self):
        """Test parsing 'in 2 hours'."""
        result = parse_natural_language_date("in 2 hours", timezone="UTC")

        assert result is not None
        assert result.day == 15
        assert result.hour == 12  # 10am + 2 hours
        assert result.minute == 0

    def test_parse_invalid_date(self):
        """Test parsing invalid date string returns None."""
        result = parse_natural_language_date("not a date", timezone="UTC")

        assert result is None

    @freeze_time("2025-01-15 10:00:00")
    def test_extract_date_from_task(self):
        """Test extracting date from task description."""
        task = "Call dentist tomorrow at 10am"
        extracted_date, cleaned_task = extract_date_from_task(task, timezone="UTC")

        assert extracted_date is not None
        assert cleaned_task == "Call dentist"
        assert extracted_date.day == 16
        assert extracted_date.hour == 10

    @freeze_time("2025-01-15 10:00:00")
    def test_extract_date_no_date_in_task(self):
        """Test extracting date when no date is present."""
        task = "Buy groceries"
        extracted_date, cleaned_task = extract_date_from_task(task, timezone="UTC")

        assert extracted_date is None
        assert cleaned_task == "Buy groceries"

    def test_datetime_to_iso(self):
        """Test converting datetime to ISO format."""
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        iso_string = datetime_to_iso(dt)

        assert iso_string == "2025-01-15T10:30:00+00:00"
        assert "T" in iso_string
        assert "+00:00" in iso_string

    def test_format_datetime_for_display(self):
        """Test formatting datetime for user-friendly display."""
        dt = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        formatted = format_datetime_for_display(dt)

        assert "Wednesday" in formatted or "2025" in formatted
        # The exact format depends on the implementation,
        # but it should be human-readable

    @freeze_time("2025-01-15 10:00:00")
    def test_is_date_in_past_true(self):
        """Test detecting past dates."""
        past_date = datetime(2025, 1, 14, 10, 0, 0, tzinfo=timezone.utc)
        assert is_date_in_past(past_date) is True

    @freeze_time("2025-01-15 10:00:00")
    def test_is_date_in_past_false(self):
        """Test detecting future dates."""
        future_date = datetime(2025, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        assert is_date_in_past(future_date) is False

    @freeze_time("2025-01-15 10:00:00")
    def test_parse_with_timezone(self):
        """Test parsing with specific timezone."""
        result = parse_natural_language_date(
            "tomorrow at 10am",
            timezone="America/New_York"
        )

        assert result is not None
        assert result.day == 16

    @freeze_time("2025-01-15 10:00:00")
    def test_parse_multiple_formats(self):
        """Test parsing various date formats."""
        test_cases = [
            "tomorrow at 10am",
            "in 3 hours",
            "today at 5:30pm",
            "Friday at 2pm",  # More reliable than "next Monday"
        ]

        for date_string in test_cases:
            result = parse_natural_language_date(date_string, timezone="UTC")
            # All of these should parse successfully
            assert result is not None, f"Failed to parse: {date_string}"
