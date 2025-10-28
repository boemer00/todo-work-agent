"""
Database connection utilities.

Provides helper functions for managing database connections and paths.
"""

import os


def get_db_path(db_name: str = "tasks.db") -> str:
    """
    Get the full path to the database file.

    Cloud-aware: Returns /tmp path on Cloud Run, data/ path locally.

    Args:
        db_name: Name of the database file

    Returns:
        Full path to the database file
    """
    # Check if running in cloud environment
    is_cloud = os.getenv("CLOUD_RUN", "false").lower() == "true"

    if is_cloud:
        # On Cloud Run, use /tmp directory (only writable location)
        return os.path.join("/tmp", db_name)
    else:
        # Locally, use data/ directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_dir = os.path.join(project_root, "data")

        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)

        return os.path.join(data_dir, db_name)
