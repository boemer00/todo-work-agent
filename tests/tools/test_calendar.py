"""Tests for Google Calendar reading functionality."""

from __future__ import annotations

import datetime as dt
from typing import Any, List

import pytest
import pytz

from tools import tasks


def _stub_datetime_now() -> dt.datetime:
    """Stub for 'now' - March 5, 2025 at 9:00 AM UTC."""
    return pytz.UTC.localize(dt.datetime(2025, 3, 5, 9, 0))


def _stub_datetime_start() -> dt.datetime:
    """Stub for 'today' start - March 5, 2025 at 00:00 UTC."""
    return pytz.UTC.localize(dt.datetime(2025, 3, 5, 0, 0))


def _stub_datetime_end() -> dt.datetime:
    """Stub for 'end of week' - March 9, 2025 at 23:59 UTC."""
    return pytz.UTC.localize(dt.datetime(2025, 3, 9, 23, 59, 59))


class TestListCalendarEvents:
    """Tests for list_calendar_events() tool wrapper."""

    def test_list_calendar_events_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful calendar event listing."""
        # Mock calendar events from Google API
        mock_events = [
            {
                'id': 'event1',
                'summary': 'Team Standup',
                'start': '2025-03-05T10:00:00Z',
                'end': '2025-03-05T10:30:00Z',
                'description': 'Daily standup meeting',
                'location': 'Zoom',
                'all_day': False
            },
            {
                'id': 'event2',
                'summary': 'Dentist Appointment',
                'start': '2025-03-06T14:00:00Z',
                'end': '2025-03-06T15:00:00Z',
                'description': 'Teeth cleaning',
                'location': '123 Main St',
                'all_day': False
            }
        ]

        # Mock date parser
        parse_calls: List[tuple[str, str]] = []

        def mock_parse(date_str: str, tz: str) -> dt.datetime:
            parse_calls.append((date_str, tz))
            if date_str == "today":
                return _stub_datetime_start()
            elif date_str == "end of week":
                return _stub_datetime_end()
            return _stub_datetime_now()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        # Mock Google Calendar API call
        from tools import google_calendar
        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            lambda start, end: mock_events
        )

        # Call the tool
        result = tasks.list_calendar_events(
            time_min="today",
            time_max="end of week",
            user_id="user-123",
            timezone="UTC"
        )

        # Assertions
        assert "📅 Your calendar" in result
        assert "2 events" in result
        assert "Team Standup" in result
        assert "Dentist Appointment" in result
        assert "Zoom" in result
        assert "123 Main St" in result

        # Verify date parsing was called
        assert len(parse_calls) == 2
        assert parse_calls[0] == ("today", "UTC")
        assert parse_calls[1] == ("end of week", "UTC")

    def test_list_calendar_events_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test calendar with no events."""
        def mock_parse(date_str: str, tz: str) -> dt.datetime:
            if date_str == "today":
                return _stub_datetime_start()
            return _stub_datetime_end()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        # Mock empty calendar
        from tools import google_calendar
        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            lambda start, end: []
        )

        result = tasks.list_calendar_events(
            time_min="today",
            time_max="end of week",
            user_id="user-123",
            timezone="UTC"
        )

        assert "No calendar events found" in result

    def test_list_calendar_events_all_day_event(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test formatting of all-day events."""
        mock_events = [
            {
                'id': 'event1',
                'summary': 'Birthday Party',
                'start': '2025-03-05T00:00:00Z',
                'end': '2025-03-05T23:59:59Z',
                'description': 'John\'s birthday',
                'location': '',
                'all_day': True
            }
        ]

        def mock_parse(date_str: str, tz: str) -> dt.datetime:
            if date_str == "today":
                return _stub_datetime_start()
            return _stub_datetime_end()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        from tools import google_calendar
        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            lambda start, end: mock_events
        )

        result = tasks.list_calendar_events(
            time_min="today",
            time_max="end of week",
            user_id="user-123",
            timezone="UTC"
        )

        assert "Birthday Party" in result
        assert "All day" in result
        assert "1 event" in result  # Singular form

    def test_list_calendar_events_credentials_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling when Google Calendar credentials are not set up."""
        def mock_parse(date_str: str, tz: str) -> dt.datetime:
            if date_str == "today":
                return _stub_datetime_start()
            return _stub_datetime_end()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        # Mock calendar service to raise FileNotFoundError
        from tools import google_calendar
        def mock_list_events(start, end):
            raise FileNotFoundError("credentials.json not found")

        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            mock_list_events
        )

        result = tasks.list_calendar_events(
            time_min="today",
            time_max="end of week",
            user_id="user-123",
            timezone="UTC"
        )

        assert "Google Calendar not configured" in result

    def test_list_calendar_events_api_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of Google Calendar API errors."""
        def mock_parse(date_str: str, tz: str) -> dt.datetime:
            if date_str == "today":
                return _stub_datetime_start()
            return _stub_datetime_end()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        # Mock calendar service to raise generic error
        from tools import google_calendar
        def mock_list_events(start, end):
            raise Exception("API quota exceeded")

        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            mock_list_events
        )

        result = tasks.list_calendar_events(
            time_min="today",
            time_max="end of week",
            user_id="user-123",
            timezone="UTC"
        )

        assert "Error fetching calendar events" in result
        assert "API quota exceeded" in result

    def test_list_calendar_events_invalid_date_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback behavior when date parsing fails."""
        mock_events = [
            {
                'id': 'event1',
                'summary': 'Meeting',
                'start': '2025-03-05T10:00:00Z',
                'end': '2025-03-05T11:00:00Z',
                'description': '',
                'location': '',
                'all_day': False
            }
        ]

        # Mock parse to return None for time_min (should fallback to 'now')
        def mock_parse(date_str: str, tz: str) -> dt.datetime | None:
            if date_str == "invalid date":
                return None  # Triggers fallback
            return _stub_datetime_end()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        from tools import google_calendar
        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            lambda start, end: mock_events
        )

        # Should not crash, should use fallback dates
        result = tasks.list_calendar_events(
            time_min="invalid date",
            time_max="end of week",
            user_id="user-123",
            timezone="UTC"
        )

        # Should succeed despite invalid input (fallback to 'today')
        assert "📅 Your calendar" in result
        assert "Meeting" in result

    def test_list_calendar_events_with_timezone(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that timezone is properly passed through."""
        parse_calls: List[tuple[str, str]] = []

        def mock_parse(date_str: str, tz: str) -> dt.datetime:
            parse_calls.append((date_str, tz))
            return _stub_datetime_start() if date_str == "today" else _stub_datetime_end()

        monkeypatch.setattr("utils.date_parser.parse_natural_language_date", mock_parse)

        from tools import google_calendar
        monkeypatch.setattr(
            google_calendar,
            "list_calendar_events",
            lambda start, end: []
        )

        tasks.list_calendar_events(
            time_min="today",
            time_max="end of week",
            user_id="user-123",
            timezone="America/New_York"
        )

        # Verify timezone was passed to date parser
        assert parse_calls[0][1] == "America/New_York"
        assert parse_calls[1][1] == "America/New_York"
