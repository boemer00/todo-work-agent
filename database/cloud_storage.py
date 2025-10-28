"""
Cloud Storage integration for database persistence.

Handles uploading/downloading SQLite databases to/from Google Cloud Storage.
This is necessary for Cloud Run since containers are stateless.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def is_cloud_environment() -> bool:
    """
    Check if running in cloud environment.

    Returns:
        bool: True if running on Cloud Run, False otherwise
    """
    return os.getenv("CLOUD_RUN", "false").lower() == "true"


def get_bucket_name() -> Optional[str]:
    """
    Get the Cloud Storage bucket name from environment.

    Returns:
        Optional[str]: Bucket name or None if not configured
    """
    return os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")


def download_database(db_name: str = "tasks.db", local_path: str = "/tmp") -> str:
    """
    Download database from Cloud Storage to local filesystem.

    This is called on application startup to restore the database state.

    Args:
        db_name: Name of the database file
        local_path: Local directory to store the database (default: /tmp for Cloud Run)

    Returns:
        str: Full path to the downloaded database file
    """
    local_db_path = os.path.join(local_path, db_name)

    # If not in cloud environment, use local data directory
    if not is_cloud_environment():
        logger.info("Not in cloud environment, using local database")
        local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(local_path, exist_ok=True)
        return os.path.join(local_path, db_name)

    bucket_name = get_bucket_name()
    if not bucket_name:
        logger.warning("GOOGLE_CLOUD_STORAGE_BUCKET not set, using local database")
        return local_db_path

    try:
        from google.cloud import storage

        # Initialize client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(db_name)

        # Create local directory if it doesn't exist
        os.makedirs(local_path, exist_ok=True)

        # Check if database exists in Cloud Storage
        if blob.exists():
            logger.info(f"Downloading {db_name} from Cloud Storage bucket {bucket_name}")
            blob.download_to_filename(local_db_path)
            logger.info(f"Downloaded database to {local_db_path}")
        else:
            logger.info(f"No existing database found in Cloud Storage, will create new one")

        return local_db_path

    except Exception as e:
        logger.error(f"Error downloading database from Cloud Storage: {e}")
        logger.info("Falling back to local database")
        return local_db_path


def upload_database(db_name: str = "tasks.db", local_path: str = "/tmp") -> bool:
    """
    Upload database from local filesystem to Cloud Storage.

    This should be called periodically and on application shutdown
    to persist the database state.

    Args:
        db_name: Name of the database file
        local_path: Local directory where the database is stored

    Returns:
        bool: True if upload successful, False otherwise
    """
    local_db_path = os.path.join(local_path, db_name)

    # If not in cloud environment, no need to upload
    if not is_cloud_environment():
        logger.debug("Not in cloud environment, skipping upload")
        return True

    bucket_name = get_bucket_name()
    if not bucket_name:
        logger.warning("GOOGLE_CLOUD_STORAGE_BUCKET not set, skipping upload")
        return False

    # Check if local database exists
    if not os.path.exists(local_db_path):
        logger.warning(f"Local database not found at {local_db_path}, skipping upload")
        return False

    try:
        from google.cloud import storage

        # Initialize client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(db_name)

        # Upload database
        logger.info(f"Uploading {db_name} to Cloud Storage bucket {bucket_name}")
        blob.upload_from_filename(local_db_path)
        logger.info(f"Successfully uploaded database to Cloud Storage")

        return True

    except Exception as e:
        logger.error(f"Error uploading database to Cloud Storage: {e}")
        return False


def sync_checkpoint_database(local_path: str = "/tmp") -> bool:
    """
    Sync the LangGraph checkpoint database with Cloud Storage.

    Args:
        local_path: Local directory where the database is stored

    Returns:
        bool: True if sync successful, False otherwise
    """
    return upload_database("checkpoints.db", local_path)


# For convenience, provide a function to get the appropriate database path
def get_cloud_db_path(db_name: str = "tasks.db") -> str:
    """
    Get the appropriate database path for the current environment.

    In cloud environments, returns /tmp/db_name
    In local environments, returns data/db_name

    Args:
        db_name: Name of the database file

    Returns:
        str: Full path to the database file
    """
    if is_cloud_environment():
        return f"/tmp/{db_name}"
    else:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, db_name)
