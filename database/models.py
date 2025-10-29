"""
Database models for task management.

Contains the Task class that handles all CRUD operations for tasks.
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Optional
from .connection import get_db_path


class TaskRepository:
    """
    Repository for managing tasks in the database.

    Handles all database operations for creating, reading, updating, and deleting tasks.
    Uses SQLite for persistence.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the TaskRepository.

        Args:
            db_path: Path to the SQLite database file. If None, uses default path.
        """
        self.db_path = db_path or get_db_path("tasks.db")
        self._init_db()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Provides automatic transaction management:
        - Commits on success
        - Rolls back on exception
        - Always closes connection

        This prioritizes simplicity and thread-safety over micro-optimization.
        SQLite connection overhead (~1ms) is negligible compared to LLM
        latency (~500ms) in this application.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """
        Initialize the database schema.

        Creates the tasks table if it doesn't exist.
        Includes migration logic for existing databases.
        """
        with self.get_connection() as conn:
            # Create table with new schema (for new databases)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    done BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date TIMESTAMP,
                    calendar_event_id TEXT,
                    timezone TEXT DEFAULT 'UTC'
                )
            """)

            # Migrate existing databases (add columns if they don't exist)
            # This is backwards-compatible and safe to run multiple times
            cursor = conn.cursor()

            # Check existing columns
            cursor.execute("PRAGMA table_info(tasks)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Add missing columns with NULL defaults (backwards compatible)
            if 'due_date' not in existing_columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP")

            if 'calendar_event_id' not in existing_columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN calendar_event_id TEXT")

            if 'timezone' not in existing_columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN timezone TEXT DEFAULT 'UTC'")

    def create_task(
        self,
        user_id: str,
        description: str,
        due_date: Optional[str] = None,
        timezone: str = "UTC"
    ) -> int:
        """
        Create a new task in the database.

        Args:
            user_id: The ID of the user creating the task
            description: The task description
            due_date: Optional ISO format datetime string for scheduled tasks
            timezone: Timezone for the task (default: UTC)

        Returns:
            The ID of the newly created task
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (user_id, description, done, due_date, timezone) VALUES (?, ?, ?, ?, ?)",
                (user_id, description, False, due_date, timezone)
            )
            task_id = cursor.lastrowid
            return task_id

    def get_user_tasks(self, user_id: str, done: bool = False) -> List[Tuple]:
        """
        Get all tasks for a specific user.

        Args:
            user_id: The ID of the user
            done: Filter by done status (False = incomplete, True = completed)

        Returns:
            List of tuples: (id, description, done, created_at, due_date, calendar_event_id, timezone)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, description, done, created_at, due_date, calendar_event_id, timezone FROM tasks WHERE user_id = ? AND done = ? ORDER BY created_at",
                (user_id, done)
            )
            tasks = cursor.fetchall()
            return tasks

    def mark_task_done(self, task_id: int, user_id: str) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: The ID of the task to mark as done
            user_id: The ID of the user (for security - can only mark own tasks)

        Returns:
            True if successful, False if task not found or doesn't belong to user
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )
            rows_affected = cursor.rowcount
            return rows_affected > 0

    def clear_all_tasks(self, user_id: str) -> int:
        """
        Delete all tasks for a user.

        Args:
            user_id: The ID of the user

        Returns:
            Number of tasks deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
            rows_affected = cursor.rowcount
            return rows_affected

    def update_calendar_event_id(self, task_id: int, user_id: str, calendar_event_id: str) -> bool:
        """
        Update the calendar event ID for a task after syncing to Google Calendar.

        Args:
            task_id: The ID of the task
            user_id: The ID of the user (for security)
            calendar_event_id: The Google Calendar event ID

        Returns:
            True if successful, False if task not found or doesn't belong to user
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET calendar_event_id = ? WHERE id = ? AND user_id = ?",
                (calendar_event_id, task_id, user_id)
            )
            rows_affected = cursor.rowcount
            return rows_affected > 0

    def get_scheduled_tasks(self, user_id: str, done: bool = False) -> List[Tuple]:
        """
        Get all tasks with due dates (scheduled tasks) for a specific user.

        Args:
            user_id: The ID of the user
            done: Filter by done status (False = incomplete, True = completed)

        Returns:
            List of tuples: (id, description, done, created_at, due_date, calendar_event_id, timezone)
            Ordered by due_date ascending (earliest first)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, description, done, created_at, due_date, calendar_event_id, timezone FROM tasks WHERE user_id = ? AND done = ? AND due_date IS NOT NULL ORDER BY due_date",
                (user_id, done)
            )
            tasks = cursor.fetchall()
            return tasks

    def get_task_by_id(self, task_id: int, user_id: str) -> Optional[Tuple]:
        """
        Get a specific task by ID.

        Args:
            task_id: The ID of the task
            user_id: The ID of the user (for security)

        Returns:
            Tuple: (id, description, done, created_at, due_date, calendar_event_id, timezone)
            or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, description, done, created_at, due_date, calendar_event_id, timezone FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )
            task = cursor.fetchone()
            return task
