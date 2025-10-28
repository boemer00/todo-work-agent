"""
Unit tests for database operations.

Tests the TaskRepository class and all CRUD operations.
"""

import pytest
from database.models import TaskRepository


@pytest.mark.unit
class TestTaskRepository:
    """Test suite for TaskRepository CRUD operations."""

    def test_create_task_basic(self, task_repo, test_user_id):
        """Test creating a basic task without due date."""
        task_id = task_repo.create_task(
            user_id=test_user_id,
            description="Buy groceries"
        )

        assert task_id is not None
        assert isinstance(task_id, int)
        assert task_id > 0

    def test_create_task_with_due_date(self, task_repo, test_user_id):
        """Test creating a task with a due date."""
        task_id = task_repo.create_task(
            user_id=test_user_id,
            description="Call dentist",
            due_date="2025-01-20T10:00:00+00:00",
            timezone="America/New_York"
        )

        assert task_id is not None

        # Verify the task was created with correct data
        task = task_repo.get_task_by_id(task_id, test_user_id)
        assert task is not None
        assert task[1] == "Call dentist"  # description
        assert task[4] == "2025-01-20T10:00:00+00:00"  # due_date
        assert task[6] == "America/New_York"  # timezone

    def test_get_user_tasks_empty(self, task_repo, test_user_id):
        """Test getting tasks when user has none."""
        tasks = task_repo.get_user_tasks(test_user_id, done=False)

        assert tasks == []
        assert len(tasks) == 0

    def test_get_user_tasks_multiple(self, task_repo, test_user_id, sample_tasks):
        """Test getting multiple tasks for a user."""
        # Create multiple tasks
        for task in sample_tasks:
            task_repo.create_task(
                user_id=task["user_id"],
                description=task["description"]
            )

        # Retrieve tasks
        tasks = task_repo.get_user_tasks(test_user_id, done=False)

        assert len(tasks) == 3
        descriptions = [task[1] for task in tasks]
        assert "Buy groceries" in descriptions
        assert "Call dentist" in descriptions
        assert "Finish report" in descriptions

    def test_user_isolation(self, task_repo):
        """Test that users only see their own tasks."""
        # Create tasks for different users
        user1_task_id = task_repo.create_task("user1", "User 1 task")
        user2_task_id = task_repo.create_task("user2", "User 2 task")

        # Check user1 sees only their task
        user1_tasks = task_repo.get_user_tasks("user1", done=False)
        assert len(user1_tasks) == 1
        assert user1_tasks[0][1] == "User 1 task"

        # Check user2 sees only their task
        user2_tasks = task_repo.get_user_tasks("user2", done=False)
        assert len(user2_tasks) == 1
        assert user2_tasks[0][1] == "User 2 task"

    def test_mark_task_done(self, task_repo, test_user_id):
        """Test marking a task as done."""
        # Create a task
        task_id = task_repo.create_task(test_user_id, "Test task")

        # Mark it as done
        success = task_repo.mark_task_done(task_id, test_user_id)
        assert success is True

        # Verify it's no longer in the incomplete list
        incomplete_tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(incomplete_tasks) == 0

        # Verify it appears in the completed list
        completed_tasks = task_repo.get_user_tasks(test_user_id, done=True)
        assert len(completed_tasks) == 1
        assert completed_tasks[0][1] == "Test task"

    def test_mark_task_done_wrong_user(self, task_repo):
        """Test that users can only mark their own tasks as done."""
        # User1 creates a task
        task_id = task_repo.create_task("user1", "User 1 task")

        # User2 tries to mark it as done (should fail)
        success = task_repo.mark_task_done(task_id, "user2")
        assert success is False

        # Verify task is still incomplete for user1
        user1_tasks = task_repo.get_user_tasks("user1", done=False)
        assert len(user1_tasks) == 1

    def test_clear_all_tasks(self, task_repo, test_user_id, sample_tasks):
        """Test clearing all tasks for a user."""
        # Create multiple tasks
        for task in sample_tasks:
            task_repo.create_task(test_user_id, task["description"])

        # Clear all tasks
        count = task_repo.clear_all_tasks(test_user_id)

        assert count == 3
        assert len(task_repo.get_user_tasks(test_user_id, done=False)) == 0

    def test_clear_all_tasks_user_isolation(self, task_repo):
        """Test that clearing tasks only affects the specified user."""
        # Create tasks for two users
        task_repo.create_task("user1", "User 1 task 1")
        task_repo.create_task("user1", "User 1 task 2")
        task_repo.create_task("user2", "User 2 task 1")

        # Clear user1's tasks
        count = task_repo.clear_all_tasks("user1")

        assert count == 2
        assert len(task_repo.get_user_tasks("user1", done=False)) == 0
        assert len(task_repo.get_user_tasks("user2", done=False)) == 1

    def test_update_calendar_event_id(self, task_repo, test_user_id):
        """Test updating the calendar event ID for a task."""
        # Create a task
        task_id = task_repo.create_task(test_user_id, "Task with calendar")

        # Update calendar event ID
        success = task_repo.update_calendar_event_id(
            task_id, test_user_id, "google_event_123"
        )

        assert success is True

        # Verify the calendar event ID was updated
        task = task_repo.get_task_by_id(task_id, test_user_id)
        assert task[5] == "google_event_123"  # calendar_event_id

    def test_get_scheduled_tasks(self, task_repo, test_user_id):
        """Test getting only tasks with due dates."""
        # Create tasks with and without due dates
        task_repo.create_task(test_user_id, "No due date")
        task_repo.create_task(
            test_user_id,
            "With due date",
            due_date="2025-01-20T10:00:00+00:00"
        )
        task_repo.create_task(
            test_user_id,
            "Another with due date",
            due_date="2025-01-21T15:00:00+00:00"
        )

        # Get only scheduled tasks
        scheduled_tasks = task_repo.get_scheduled_tasks(test_user_id, done=False)

        assert len(scheduled_tasks) == 2
        # Verify they're ordered by due date (earliest first)
        assert scheduled_tasks[0][1] == "With due date"
        assert scheduled_tasks[1][1] == "Another with due date"

    def test_get_task_by_id(self, task_repo, test_user_id):
        """Test retrieving a specific task by ID."""
        task_id = task_repo.create_task(test_user_id, "Specific task")

        task = task_repo.get_task_by_id(task_id, test_user_id)

        assert task is not None
        assert task[0] == task_id
        assert task[1] == "Specific task"

    def test_get_task_by_id_wrong_user(self, task_repo):
        """Test that users can only access their own tasks."""
        task_id = task_repo.create_task("user1", "User 1 task")

        # User2 tries to access user1's task
        task = task_repo.get_task_by_id(task_id, "user2")

        assert task is None
