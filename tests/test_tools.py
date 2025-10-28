"""
Unit tests for task management tools.

Tests all tool functions that the agent can call.
"""

import pytest
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

from tools.tasks import (
    add_task,
    list_tasks,
    mark_task_done,
    clear_all_tasks,
    create_reminder
)
from database.models import TaskRepository


@pytest.mark.unit
class TestAddTask:
    """Test suite for add_task tool."""

    def test_add_task_success(self, task_repo, test_user_id, mocker):
        """Test adding a task successfully."""
        # Patch the global task_repo in the tools module
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = add_task(task="Buy groceries", user_id=test_user_id)

        assert "✓" in result or "Added" in result
        assert "Buy groceries" in result

        # Verify task was actually created
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1
        assert tasks[0][1] == "Buy groceries"

    def test_add_task_multiple(self, task_repo, test_user_id, mocker):
        """Test adding multiple tasks."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        add_task(task="Task 1", user_id=test_user_id)
        add_task(task="Task 2", user_id=test_user_id)
        add_task(task="Task 3", user_id=test_user_id)

        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 3


@pytest.mark.unit
class TestListTasks:
    """Test suite for list_tasks tool."""

    def test_list_tasks_empty(self, task_repo, test_user_id, mocker):
        """Test listing tasks when none exist."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = list_tasks(user_id=test_user_id)

        assert "no tasks" in result.lower() or "🎉" in result

    def test_list_tasks_with_items(self, task_repo, test_user_id, sample_tasks, mocker):
        """Test listing multiple tasks."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Create tasks
        for task in sample_tasks:
            task_repo.create_task(test_user_id, task["description"])

        result = list_tasks(user_id=test_user_id)

        assert "Buy groceries" in result
        assert "Call dentist" in result
        assert "Finish report" in result

    def test_list_tasks_with_due_dates(self, task_repo, test_user_id, mocker):
        """Test listing tasks shows due dates when present."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Create task with due date
        task_repo.create_task(
            test_user_id,
            "Call dentist",
            due_date="2025-01-20T10:00:00+00:00"
        )

        result = list_tasks(user_id=test_user_id)

        assert "Call dentist" in result
        assert "Due:" in result or "2025" in result


@pytest.mark.unit
class TestMarkTaskDone:
    """Test suite for mark_task_done tool."""

    def test_mark_task_done_success(self, task_repo, test_user_id, mocker):
        """Test marking a task as done successfully."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Create a task
        task_repo.create_task(test_user_id, "Test task")

        # Mark it as done
        result = mark_task_done(task_number=1, user_id=test_user_id)

        assert "✓" in result or "Marked" in result
        assert "Test task" in result

        # Verify task is marked done
        incomplete_tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(incomplete_tasks) == 0

    def test_mark_task_done_invalid_number(self, task_repo, test_user_id, mocker):
        """Test marking task with invalid task number."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Create one task
        task_repo.create_task(test_user_id, "Test task")

        # Try to mark task #5 (doesn't exist)
        result = mark_task_done(task_number=5, user_id=test_user_id)

        assert "❌" in result or "Invalid" in result

    def test_mark_task_done_no_tasks(self, task_repo, test_user_id, mocker):
        """Test marking task done when no tasks exist."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = mark_task_done(task_number=1, user_id=test_user_id)

        assert "❌" in result or "no tasks" in result.lower()

    def test_mark_task_done_with_calendar_event(
        self, task_repo, test_user_id, mock_google_calendar, mocker
    ):
        """Test marking done a task that has a calendar event."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Create task with calendar event ID
        task_id = task_repo.create_task(test_user_id, "Task with calendar")
        task_repo.update_calendar_event_id(task_id, test_user_id, "calendar_event_123")

        # Mark done
        result = mark_task_done(task_number=1, user_id=test_user_id)

        # Verify calendar event deletion was attempted
        mock_google_calendar['delete'].assert_called_once_with("calendar_event_123")


@pytest.mark.unit
class TestClearAllTasks:
    """Test suite for clear_all_tasks tool."""

    def test_clear_all_tasks_success(self, task_repo, test_user_id, sample_tasks, mocker):
        """Test clearing all tasks."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Create tasks
        for task in sample_tasks:
            task_repo.create_task(test_user_id, task["description"])

        result = clear_all_tasks(user_id=test_user_id)

        assert "✓" in result or "Cleared" in result
        assert "3" in result

        # Verify all tasks cleared
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 0

    def test_clear_all_tasks_empty(self, task_repo, test_user_id, mocker):
        """Test clearing when no tasks exist."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = clear_all_tasks(user_id=test_user_id)

        assert "no tasks" in result.lower()


@pytest.mark.unit
class TestCreateReminder:
    """Test suite for create_reminder tool."""

    @freeze_time("2025-01-15 10:00:00")
    def test_create_reminder_success(
        self, task_repo, test_user_id, mock_google_calendar, mocker
    ):
        """Test creating a reminder successfully."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = create_reminder(
            task="Call dentist",
            when="tomorrow at 10am",
            user_id=test_user_id,
            timezone="UTC"
        )

        assert "✓" in result or "Reminder set" in result
        assert "Call dentist" in result

        # Verify task was created with due date
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1
        assert tasks[0][1] == "Call dentist"
        assert tasks[0][4] is not None  # has due_date

        # Verify calendar event was created
        mock_google_calendar['create'].assert_called_once()

    @freeze_time("2025-01-15 10:00:00")
    def test_create_reminder_invalid_date(self, task_repo, test_user_id, mocker):
        """Test creating reminder with invalid date."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = create_reminder(
            task="Call dentist",
            when="not a valid date",
            user_id=test_user_id,
            timezone="UTC"
        )

        assert "❌" in result or "Couldn't understand" in result

    @freeze_time("2025-01-15 10:00:00")
    def test_create_reminder_past_date(self, task_repo, test_user_id, mocker):
        """Test creating reminder with past date."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = create_reminder(
            task="Call dentist",
            when="yesterday at 10am",
            user_id=test_user_id,
            timezone="UTC"
        )

        assert "❌" in result or "past" in result.lower()

    @freeze_time("2025-01-15 10:00:00")
    def test_create_reminder_calendar_unavailable(
        self, task_repo, test_user_id, mocker
    ):
        """Test creating reminder when Google Calendar is unavailable."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Mock calendar to raise FileNotFoundError (credentials not found)
        mock_create = mocker.patch('tools.tasks.create_calendar_event')
        mock_create.side_effect = FileNotFoundError("credentials.json not found")

        result = create_reminder(
            task="Call dentist",
            when="tomorrow at 10am",
            user_id=test_user_id,
            timezone="UTC"
        )

        # Task should still be created locally
        assert "✓" in result or "added locally" in result.lower()
        assert "⚠️" in result or "not configured" in result.lower()

        # Verify task was created despite calendar failure
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1

    @freeze_time("2025-01-15 10:00:00")
    def test_create_reminder_with_timezone(
        self, task_repo, test_user_id, mock_google_calendar, mocker
    ):
        """Test creating reminder with specific timezone."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        result = create_reminder(
            task="Team meeting",
            when="tomorrow at 2pm",
            user_id=test_user_id,
            timezone="America/New_York"
        )

        assert "✓" in result

        # Verify timezone was stored
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert tasks[0][6] == "America/New_York"  # timezone field
