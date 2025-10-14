"""
Database models for task management.

Contains the Task class that handles all CRUD operations for tasks.
"""

import sqlite3
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

    def _init_db(self):
        """
        Initialize the database schema.

        Creates the tasks table if it doesn't exist.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                description TEXT NOT NULL,
                done BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def create_task(self, user_id: str, description: str) -> int:
        """
        Create a new task in the database.

        Args:
            user_id: The ID of the user creating the task
            description: The task description

        Returns:
            The ID of the newly created task
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, description, done) VALUES (?, ?, ?)",
            (user_id, description, False)
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def get_user_tasks(self, user_id: str, done: bool = False) -> List[Tuple]:
        """
        Get all tasks for a specific user.

        Args:
            user_id: The ID of the user
            done: Filter by done status (False = incomplete, True = completed)

        Returns:
            List of tuples: (id, description, done, created_at)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, description, done, created_at FROM tasks WHERE user_id = ? AND done = ? ORDER BY created_at",
            (user_id, done)
        )
        tasks = cursor.fetchall()
        conn.close()
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0

    def clear_all_tasks(self, user_id: str) -> int:
        """
        Delete all tasks for a user.

        Args:
            user_id: The ID of the user

        Returns:
            Number of tasks deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected
