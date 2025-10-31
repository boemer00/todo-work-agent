"""Tests for `tools.tasks` functions."""

from __future__ import annotations

import datetime as dt
from typing import Any, List, Optional

import pytest
import pytz

from tools import tasks


def _stub_datetime() -> dt.datetime:
    return pytz.UTC.localize(dt.datetime(2025, 3, 5, 9, 0))


def test_create_reminder_with_calendar_success(monkeypatch: pytest.MonkeyPatch) -> None:
    created_payload: dict[str, Any] = {}
    updated: Optional[tuple[int, str, str]] = None

    class Repo:
        def create_task(self, user_id: str, description: str, due_date: str, timezone: str) -> int:
            created_payload.update(
                {
                    "user_id": user_id,
                    "description": description,
                    "due_date": due_date,
                    "timezone": timezone,
                }
            )
            return 7

        def update_calendar_event_id(self, task_id: int, user_id: str, calendar_event_id: str) -> None:
            nonlocal updated
            updated = (task_id, user_id, calendar_event_id)

    repo = Repo()
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo)
    monkeypatch.setattr("utils.date_parser.parse_natural_language_date", lambda when, timezone: _stub_datetime())
    monkeypatch.setattr(tasks, "is_date_in_past", lambda dt_obj: False)
    monkeypatch.setattr(
        tasks,
        "create_calendar_event",
        lambda summary, start_datetime, description: "event-123",
    )

    message = tasks.create_reminder("call mom", "tomorrow", "user-1", timezone="UTC")

    assert "Reminder set" in message
    assert created_payload["description"] == "call mom"
    assert updated == (7, "user-1", "event-123")


def test_create_reminder_handles_calendar_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def __init__(self) -> None:
            self.updated: List[Any] = []

        def create_task(self, user_id: str, description: str, due_date: str, timezone: str) -> int:
            return 9

        def update_calendar_event_id(self, task_id: int, user_id: str, calendar_event_id: str) -> None:
            self.updated.append((task_id, user_id, calendar_event_id))

    repo = Repo()
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo)
    monkeypatch.setattr("utils.date_parser.parse_natural_language_date", lambda *args, **kwargs: _stub_datetime())
    monkeypatch.setattr(tasks, "is_date_in_past", lambda dt_obj: False)
    monkeypatch.setattr(tasks, "create_calendar_event", lambda **kwargs: None)

    message = tasks.create_reminder("call mom", "tomorrow", "user-1")

    assert "Couldn't add to Google Calendar" in message
    assert repo.updated == []


def test_create_reminder_rejects_past_or_unparsed_times(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def __init__(self) -> None:
            self.created = 0

        def create_task(self, *args, **kwargs):  # pragma: no cover - shouldn't be hit when parse fails
            self.created += 1

    repo = Repo()
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo)
    monkeypatch.setattr("utils.date_parser.parse_natural_language_date", lambda *args, **kwargs: None)

    message = tasks.create_reminder("call mom", "someday", "user-1")

    assert "Couldn't understand" in message
    assert repo.created == 0

    monkeypatch.setattr("utils.date_parser.parse_natural_language_date", lambda *args, **kwargs: _stub_datetime())
    monkeypatch.setattr(tasks, "is_date_in_past", lambda dt_obj: True)

    message_past = tasks.create_reminder("call mom", "yesterday", "user-1")

    assert "in the past" in message_past
    assert repo.created == 0


def test_create_reminder_handles_missing_calendar_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def create_task(self, *args, **kwargs) -> int:
            return 5

    repo = Repo()
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo)
    monkeypatch.setattr("utils.date_parser.parse_natural_language_date", lambda *args, **kwargs: _stub_datetime())
    monkeypatch.setattr(tasks, "is_date_in_past", lambda dt_obj: False)

    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("credentials missing")

    monkeypatch.setattr(tasks, "create_calendar_event", raise_file_not_found)

    message = tasks.create_reminder("call mom", "tomorrow", "user-1")

    assert "Google Calendar not configured" in message


def test_create_reminder_handles_general_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def create_task(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(tasks, "TaskRepository", lambda: Repo())
    monkeypatch.setattr("utils.date_parser.parse_natural_language_date", lambda *args, **kwargs: _stub_datetime())
    monkeypatch.setattr(tasks, "is_date_in_past", lambda dt_obj: False)

    message = tasks.create_reminder("call mom", "tomorrow", "user-1")

    assert message.startswith("❌ Error creating reminder: boom")


def test_add_task_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def create_task(self, user_id: str, description: str) -> int:
            assert user_id == "user-1"
            assert description == "buy milk"
            return 3

    monkeypatch.setattr(tasks, "TaskRepository", lambda: Repo())

    message = tasks.add_task("buy milk", "user-1")

    assert message == "✓ Added task #3: 'buy milk'"


def test_add_task_handles_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def create_task(self, *args, **kwargs):
            raise ValueError("duplicate")

    monkeypatch.setattr(tasks, "TaskRepository", lambda: Repo())

    message = tasks.add_task("buy milk", "user-1")

    assert message == "❌ Error adding task: duplicate"


def test_list_tasks_with_due_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def get_user_tasks(self, user_id: str, done: bool = False):
            assert user_id == "user-1"
            assert done is False
            return [
                (1, "Task A", False, "created", "2025-03-05T09:00:00+00:00", None, "UTC"),
            ]

    monkeypatch.setattr(tasks, "TaskRepository", lambda: Repo())
    monkeypatch.setattr(tasks, "iso_to_datetime", lambda iso: _stub_datetime())
    monkeypatch.setattr(tasks, "format_datetime_relative", lambda dt_obj, tz: "Due soon")

    message = tasks.list_tasks("user-1")

    assert "1. Task A (Due: Due soon)" in message


def test_list_tasks_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def get_user_tasks(self, user_id: str, done: bool = False):
            return []

    monkeypatch.setattr(tasks, "TaskRepository", lambda: Repo())

    assert tasks.list_tasks("user-1") == "You have no tasks! 🎉"


def test_list_tasks_fallback_to_raw_due_date(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def get_user_tasks(self, user_id: str, done: bool = False):
            return [
                (1, "Task A", False, "created", "RAWDATE", None, "UTC"),
            ]

    monkeypatch.setattr(tasks, "TaskRepository", lambda: Repo())

    def raise_parse_error(_iso: str):
        raise ValueError("bad format")

    monkeypatch.setattr(tasks, "iso_to_datetime", raise_parse_error)

    message = tasks.list_tasks("user-1")

    assert "RAWDATE" in message


def test_mark_task_done_success_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def __init__(self, calendar_event_id: Optional[str]) -> None:
            self.calendar_event_id = calendar_event_id
            self.mark_calls: list[tuple[int, str]] = []

        def get_user_tasks(self, user_id: str, done: bool = False):
            return [
                (1, "Task", False, "created", None, self.calendar_event_id, "UTC"),
            ]

        def mark_task_done(self, task_id: int, user_id: str) -> bool:
            self.mark_calls.append((task_id, user_id))
            return True

    # Scenario: calendar deletion succeeds
    repo_with_calendar = Repo("cal-1")
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo_with_calendar)
    monkeypatch.setattr(tasks, "delete_calendar_event", lambda event_id: True)

    message = tasks.mark_task_done(1, "user-1")

    assert "Marked task #1" in message
    assert "Removed from Google Calendar" in message
    assert repo_with_calendar.mark_calls == [(1, "user-1")]

    # Scenario: calendar deletion fails but should still succeed
    repo_without_calendar = Repo("cal-2")
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo_without_calendar)

    def raise_delete_error(event_id: str) -> None:
        raise RuntimeError("delete failed")

    monkeypatch.setattr(tasks, "delete_calendar_event", raise_delete_error)

    message_no_calendar = tasks.mark_task_done(1, "user-2")

    assert "Removed from Google Calendar" not in message_no_calendar
    assert repo_without_calendar.mark_calls == [(1, "user-2")]


def test_mark_task_done_validates_input(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def __init__(self, tasks_list: List[tuple]) -> None:
            self.tasks = tasks_list

        def get_user_tasks(self, user_id: str, done: bool = False):
            return self.tasks

        def mark_task_done(self, *args, **kwargs) -> bool:
            return False

    # No tasks available
    repo_empty = Repo([])
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo_empty)
    assert tasks.mark_task_done(1, "user-1") == "❌ You have no tasks to mark as done."

    # Invalid index
    repo_with_tasks = Repo([(1, "Task", False, "created", None, None, "UTC")])
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo_with_tasks)
    assert "Invalid task number" in tasks.mark_task_done(2, "user-1")

    # Failed to mark task as done (returns False)
    assert tasks.mark_task_done(1, "user-1") == "❌ Failed to mark task as done."


def test_clear_all_tasks_confirmation_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    class Repo:
        def __init__(self) -> None:
            self.tasks: List[tuple] = []
            self.cleared: int = 0

        def get_user_tasks(self, user_id: str, done: bool = False):
            return self.tasks

        def clear_all_tasks(self, user_id: str) -> int:
            return self.cleared

    repo = Repo()
    monkeypatch.setattr(tasks, "TaskRepository", lambda: repo)

    # No tasks
    repo.tasks = []
    assert tasks.clear_all_tasks("user-1") == "You have no tasks to clear."

    # One task, not confirmed
    repo.tasks = [(1, "Task", False, "created", None, None, "UTC")]
    assert "delete your 1 task" in tasks.clear_all_tasks("user-1", confirmed=False)

    # Multiple tasks prompt
    repo.tasks = [
        (1, "Task", False, "created", None, None, "UTC"),
        (2, "Task", False, "created", None, None, "UTC"),
    ]
    assert "delete all 2 tasks" in tasks.clear_all_tasks("user-1", confirmed=False)

    # Confirmed deletion
    repo.cleared = 2
    assert tasks.clear_all_tasks("user-1", confirmed=True) == "✓ Cleared 2 tasks!"
