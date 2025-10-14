"""
Database connection utilities.

Provides helper functions for managing database connections and paths.
"""

import os


def get_db_path(db_name: str = "tasks.db") -> str:
    """
    Get the full path to the database file.

    Args:
        db_name: Name of the database file

    Returns:
        Full path to the database file in the data/ directory
    """
    # Get the project root (parent of this file's directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_dir = os.path.join(project_root, "data")

    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    return os.path.join(data_dir, db_name)
