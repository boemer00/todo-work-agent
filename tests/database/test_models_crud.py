"""Tests for `database.models.TaskRepository` CRUD logic."""

from __future__ import annotations

import datetime as dt

import pytz

from database.models import TaskRepository
from utils.date_parser import datetime_to_iso


def _repo(tmp_path) -> TaskRepository:
    db_file = tmp_path / "tasks.sqlite"
    return TaskRepository(db_path=str(db_file))


def test_create_task_persists_record(tmp_path) -> None:
    repo = _repo(tmp_path)
    task_id = repo.create_task("user-1", "Call mom", timezone="America/New_York")

    tasks = repo.get_user_tasks("user-1")

    assert task_id == tasks[0][0]
    assert tasks[0][1] == "Call mom"
    assert tasks[0][6] == "America/New_York"


def test_get_user_tasks_orders_by_created_at(tmp_path) -> None:
    repo = _repo(tmp_path)
    repo.create_task("user-1", "First task")
    repo.create_task("user-1", "Second task")

    descriptions = [task[1] for task in repo.get_user_tasks("user-1")]

    assert descriptions == ["First task", "Second task"]


def test_mark_task_done_updates_status(tmp_path) -> None:
    repo = _repo(tmp_path)
    task_id = repo.create_task("user-1", "Task to finish")

    assert repo.mark_task_done(task_id, "user-1") is True
    assert repo.mark_task_done(task_id, "other-user") is False

    completed = repo.get_user_tasks("user-1", done=True)
    assert completed and completed[0][0] == task_id


def test_update_calendar_event_id_assigns_identifier(tmp_path) -> None:
    repo = _repo(tmp_path)
    task_id = repo.create_task("user-1", "Task with calendar")

    assert repo.update_calendar_event_id(task_id, "user-1", "event-123") is True
    fetched = repo.get_task_by_id(task_id, "user-1")

    assert fetched[5] == "event-123"
    assert repo.update_calendar_event_id(task_id, "other", "event-456") is False


def test_get_scheduled_tasks_filters_and_sorts(tmp_path) -> None:
    repo = _repo(tmp_path)
    first_due = datetime_to_iso(pytz.UTC.localize(dt.datetime(2025, 3, 5, 9, 0)))
    second_due = datetime_to_iso(pytz.UTC.localize(dt.datetime(2025, 3, 6, 9, 0)))

    repo.create_task("user-1", "Unsheduled")
    repo.create_task("user-1", "First", due_date=second_due)
    repo.create_task("user-1", "Second", due_date=first_due)

    scheduled = repo.get_scheduled_tasks("user-1")
    descriptions = [task[1] for task in scheduled]

    assert descriptions == ["Second", "First"]


def test_get_task_by_id_returns_tuple(tmp_path) -> None:
    repo = _repo(tmp_path)
    task_id = repo.create_task("user-1", "Lookup task")

    fetched = repo.get_task_by_id(task_id, "user-1")
    assert fetched[1] == "Lookup task"
    assert repo.get_task_by_id(task_id, "other-user") is None


def test_clear_all_tasks_deletes_records(tmp_path) -> None:
    repo = _repo(tmp_path)
    repo.create_task("user-1", "Task A")
    repo.create_task("user-1", "Task B")

    deleted_count = repo.clear_all_tasks("user-1")
    assert deleted_count == 2
    assert repo.get_user_tasks("user-1") == []
