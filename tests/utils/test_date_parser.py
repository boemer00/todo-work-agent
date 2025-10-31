"""Tests for `utils.date_parser` helpers."""

from __future__ import annotations

import datetime as dt

import pytz
from freezegun import freeze_time

from utils import date_parser


@freeze_time("2025-03-01 12:00:00", tz_offset=0)
def test_parse_natural_language_date_future_reference() -> None:
    result = date_parser.parse_natural_language_date("tomorrow at 10am", timezone="UTC")
    expected = pytz.UTC.localize(dt.datetime(2025, 3, 2, 10, 0))

    assert result == expected


def test_parse_natural_language_date_no_match_returns_none() -> None:
    result = date_parser.parse_natural_language_date("no dates here", timezone="UTC")

    assert result is None


@freeze_time("2025-03-01 08:00:00", tz_offset=0)
def test_extract_date_from_task_with_temporal_phrase() -> None:
    parsed, cleaned = date_parser.extract_date_from_task("call mom tomorrow at 9am", timezone="UTC")

    assert parsed == pytz.UTC.localize(dt.datetime(2025, 3, 2, 9, 0))
    assert cleaned == "Call mom"


def test_extract_date_from_task_without_temporal_phrase() -> None:
    parsed, cleaned = date_parser.extract_date_from_task("Read book", timezone="UTC")

    assert parsed is None
    assert cleaned == "Read book"


def test_is_date_in_past_detection() -> None:
    now = pytz.UTC.localize(dt.datetime.utcnow())
    past = now - dt.timedelta(days=1)
    future = now + dt.timedelta(days=1)

    assert date_parser.is_date_in_past(past) is True
    assert date_parser.is_date_in_past(future) is False


def test_format_datetime_for_display_human_readable() -> None:
    sample = pytz.UTC.localize(dt.datetime(2025, 3, 1, 14, 30))

    assert date_parser.format_datetime_for_display(sample) == "Saturday, March 01, 2025 at 02:30 PM"


@freeze_time("2025-03-10 09:00:00", tz_offset=0)
def test_format_datetime_relative_variants() -> None:
    tz = "UTC"
    today = pytz.UTC.localize(dt.datetime(2025, 3, 10, 15, 0))
    tomorrow = pytz.UTC.localize(dt.datetime(2025, 3, 11, 10, 0))
    later = pytz.UTC.localize(dt.datetime(2025, 3, 15, 18, 30))
    overdue = pytz.UTC.localize(dt.datetime(2025, 3, 9, 12, 0))

    assert date_parser.format_datetime_relative(today, tz) == "Today at 3:00 PM"
    assert date_parser.format_datetime_relative(tomorrow, tz) == "Tomorrow at 10:00 AM"
    assert date_parser.format_datetime_relative(later, tz).startswith("Saturday, 15 Mar at")
    assert date_parser.format_datetime_relative(overdue, tz).startswith("⚠️ OVERDUE: ")


def test_iso_conversion_round_trip() -> None:
    original = pytz.UTC.localize(dt.datetime(2025, 7, 4, 9, 45, 13))
    serialized = date_parser.datetime_to_iso(original)
    restored = date_parser.iso_to_datetime(serialized)

    assert restored == original
