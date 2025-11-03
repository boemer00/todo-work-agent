"""
Date parsing utilities for extracting dates/times from natural language.

Handles phrases like:
- "tomorrow at 10am"
- "next Friday at 2pm"
- "in 3 days at 5:30pm"
- "January 15th at 9am"
- "call Gabi tomorrow at 10am"

Uses dateparser library for robust, deterministic parsing.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import dateparser
import pytz


def parse_natural_language_date(
    text: str,
    timezone: str = "UTC",
    prefer_future: bool = True
) -> Optional[datetime]:
    """
    Parse a natural language date/time string into a datetime object.

    Args:
        text: The text containing a date/time reference
        timezone: The timezone to use for interpretation (default: UTC)
        prefer_future: If True, ambiguous dates default to future (default: True)

    Returns:
        Timezone-aware datetime object, or None if no date found

    Examples:
        >>> parse_natural_language_date("tomorrow at 10am", "America/New_York")
        datetime(2025, 10, 28, 10, 0, tzinfo=...)

        >>> parse_natural_language_date("next Friday 2pm")
        datetime(2025, 10, 31, 14, 0, tzinfo=...)

        >>> parse_natural_language_date("in 3 hours")
        datetime(2025, 10, 27, 17, 30, tzinfo=...)
    """
    # Configure dateparser settings
    settings = {
        'PREFER_DATES_FROM': 'future' if prefer_future else 'current_period',
        'TIMEZONE': timezone,
        'RETURN_AS_TIMEZONE_AWARE': True,
        'TO_TIMEZONE': timezone,
    }

    # Parse the date
    parsed_date = dateparser.parse(text, settings=settings)  # type: ignore[arg-type]

    # If parsing failed, return None
    if not parsed_date:
        return None

    # Ensure timezone-aware (fallback if dateparser didn't apply it)
    if parsed_date.tzinfo is None:
        tz = pytz.timezone(timezone)
        parsed_date = tz.localize(parsed_date)

    return parsed_date


def extract_date_from_task(
    task_description: str,
    timezone: str = "UTC"
) -> Tuple[Optional[datetime], str]:
    """
    Extract a date/time from a task description and return cleaned description.

    This function attempts to find temporal expressions in the task description
    and separates them from the actual task content.

    Args:
        task_description: The full task description (e.g., "call Gabi tomorrow at 10am")
        timezone: The timezone to use for interpretation

    Returns:
        Tuple of (parsed_datetime, cleaned_description)
        - parsed_datetime: The extracted datetime, or None if no date found
        - cleaned_description: The task description with date/time phrases removed

    Examples:
        >>> extract_date_from_task("call Gabi tomorrow at 10am")
        (datetime(...), "call Gabi")

        >>> extract_date_from_task("buy groceries next Friday 2pm")
        (datetime(...), "buy groceries")

        >>> extract_date_from_task("read book")
        (None, "read book")
    """
    import re

    # Define temporal patterns to extract and parse separately
    # Ordered from most specific to least specific
    temporal_patterns = [
        # Match "tomorrow at 10am", "today at 2pm", etc.
        r'\b(tomorrow|today|tonight)\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)\b',
        # Match "next Friday at 2pm", "next Monday at 10am", etc.
        r'\bnext\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)\b',
        # Match "next week/month/year at time"
        r'\bnext\s+(?:week|month|year)\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)\b',
        # Match "next week/month/year/day" without time
        r'\bnext\s+(?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        # Match "in 3 hours", "in 2 days", etc.
        r'\bin\s+\d+\s+(?:minute|minutes|hour|hours|day|days|week|weeks|month|months)\b',
        # Match standalone times "at 10am", "at 2:30pm"
        r'\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)\b',
        # Match just "tomorrow", "today", "tonight"
        r'\b(tomorrow|today|tonight)\b',
    ]

    parsed_date = None
    temporal_match = None

    # Try each pattern to find temporal expressions
    for pattern in temporal_patterns:
        match = re.search(pattern, task_description, re.IGNORECASE)
        if match:
            temporal_text = match.group(0)
            # Try to parse just the temporal portion
            parsed_date = parse_natural_language_date(temporal_text, timezone)
            if parsed_date:
                temporal_match = match
                break

    # If no pattern matched, try parsing the whole text as fallback
    if not parsed_date:
        parsed_date = parse_natural_language_date(task_description, timezone)
        if not parsed_date:
            # No date found at all
            return None, task_description
        else:
            # Parsed the whole thing, but can't separate task from date
            # Return as-is
            return parsed_date, task_description

    # Remove the temporal expression from the description
    if temporal_match:
        cleaned = task_description[:temporal_match.start()] + task_description[temporal_match.end():]
    else:
        cleaned = task_description

    # Clean up whitespace
    cleaned = ' '.join(cleaned.split()).strip()

    # If we removed too much (less than 2 chars left), return original
    if len(cleaned) < 2:
        return parsed_date, task_description

    # Capitalize first letter
    cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else task_description

    return parsed_date, cleaned


def is_date_in_past(dt: datetime) -> bool:
    """
    Check if a datetime is in the past.

    Args:
        dt: Timezone-aware datetime object

    Returns:
        True if the datetime is in the past, False otherwise
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    return dt < now


def format_datetime_for_display(dt: datetime) -> str:
    """
    Format a datetime for user-friendly display.

    Args:
        dt: Timezone-aware datetime object

    Returns:
        Human-readable datetime string

    Examples:
        >>> format_datetime_for_display(datetime(2025, 10, 28, 10, 0))
        "Tuesday, October 28, 2025 at 10:00 AM"
    """
    return dt.strftime("%A, %B %d, %Y at %I:%M %p")


def format_datetime_relative(dt: datetime, timezone: str = "UTC") -> str:
    """
    Format a datetime with relative dates (Today, Tomorrow) when applicable.

    Shows:
    - "Today at 10:00 AM" for today
    - "Tomorrow at 10:00 AM" for tomorrow
    - "Tuesday, 28 Oct at 10:00 AM" for other dates
    - Adds "⚠️ OVERDUE" prefix if date is in the past

    Args:
        dt: Timezone-aware datetime object
        timezone: Timezone for comparison (default: UTC)

    Returns:
        Human-readable datetime string with relative dates

    Examples:
        >>> format_datetime_relative(datetime(2025, 10, 28, 10, 0))
        "Tomorrow at 10:00 AM"
    """
    # Get current time in the same timezone as dt
    tz = pytz.timezone(timezone) if timezone else dt.tzinfo
    now = datetime.now(tz)

    # Check if overdue
    is_overdue = dt < now
    prefix = "⚠️ OVERDUE: " if is_overdue else ""

    # Calculate difference in days (ignoring time)
    dt_date = dt.date()
    now_date = now.date()
    days_diff = (dt_date - now_date).days

    # Format time part
    time_str = dt.strftime("%I:%M %p").lstrip('0')  # Remove leading zero

    # Format based on relative date
    if days_diff == 0:
        return f"{prefix}Today at {time_str}"
    elif days_diff == 1:
        return f"{prefix}Tomorrow at {time_str}"
    else:
        # Show day name and short date for near future
        date_str = dt.strftime("%A, %d %b at")
        return f"{prefix}{date_str} {time_str}"


def datetime_to_iso(dt: datetime) -> str:
    """
    Convert datetime to ISO 8601 format string (for database storage).

    Args:
        dt: Timezone-aware datetime object

    Returns:
        ISO format string

    Examples:
        >>> datetime_to_iso(datetime(2025, 10, 28, 10, 0, tzinfo=pytz.UTC))
        "2025-10-28T10:00:00+00:00"
    """
    return dt.isoformat()


def _normalize_iso_utc_z(iso_string: str) -> str:
    """
    Normalize trailing 'Z' (UTC) to '+00:00' for datetime.fromisoformat compatibility.

    Args:
        iso_string: ISO 8601 datetime string, possibly ending with 'Z'

    Returns:
        Normalized ISO string compatible with datetime.fromisoformat
    """
    s = iso_string.strip()
    if s.endswith("Z"):
        return s[:-1] + "+00:00"
    return s


def iso_to_datetime(iso_string: str) -> datetime:
    """
    Convert ISO 8601 format string to datetime object.

    Accepts both timezone-offset formats and trailing 'Z' (UTC) by normalizing
    to '+00:00' before parsing.

    Args:
        iso_string: ISO format datetime string

    Returns:
        Timezone-aware datetime object

    Examples:
        >>> iso_to_datetime("2025-10-28T10:00:00+00:00")
        datetime(2025, 10, 28, 10, 0, tzinfo=...)
        >>> iso_to_datetime("2025-10-28T10:00:00Z")
        datetime(2025, 10, 28, 10, 0, tzinfo=...)
    """
    normalized = _normalize_iso_utc_z(iso_string)
    return datetime.fromisoformat(normalized)
