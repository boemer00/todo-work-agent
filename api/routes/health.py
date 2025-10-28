"""Health check endpoints."""

import os
from fastapi import APIRouter
from database.connection import get_db_path

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check endpoint for Cloud Run and monitoring.

    Returns:
        dict: Health status and database connection status
    """
    try:
        # Test database path exists
        db_path = get_db_path("tasks.db")
        db_exists = os.path.exists(db_path)

        return {
            "status": "healthy",
            "database": "accessible" if db_exists else "not_initialized",
            "service": "ai-task-agent"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
