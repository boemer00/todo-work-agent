"""FastAPI application for WhatsApp integration."""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI

from api.routes import whatsapp, health
from database.cloud_storage import (
    download_database,
    upload_database,
    sync_checkpoint_database,
    is_cloud_environment
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.

    Startup:
    - Downloads databases from Cloud Storage (if in cloud environment)

    Shutdown:
    - Uploads databases to Cloud Storage (if in cloud environment)
    """
    # Startup: Download databases from Cloud Storage
    logger.info("Starting application...")

    if is_cloud_environment():
        logger.info("Running in cloud environment, downloading databases...")
        try:
            # Download task database
            db_path = download_database("tasks.db", "/tmp")
            logger.info(f"Task database ready at: {db_path}")

            # Download checkpoint database
            checkpoint_path = download_database("checkpoints.db", "/tmp")
            logger.info(f"Checkpoint database ready at: {checkpoint_path}")
        except Exception as e:
            logger.error(f"Error downloading databases: {e}")
            logger.info("Continuing with empty databases")
    else:
        logger.info("Running locally, using local databases")

    logger.info("Application started successfully")

    # Yield control to the application
    yield

    # Shutdown: Upload databases to Cloud Storage
    logger.info("Shutting down application...")

    if is_cloud_environment():
        logger.info("Uploading databases to Cloud Storage...")
        try:
            # Upload task database
            upload_success = upload_database("tasks.db", "/tmp")
            if upload_success:
                logger.info("Task database uploaded successfully")
            else:
                logger.warning("Failed to upload task database")

            # Upload checkpoint database
            checkpoint_success = sync_checkpoint_database("/tmp")
            if checkpoint_success:
                logger.info("Checkpoint database uploaded successfully")
            else:
                logger.warning("Failed to upload checkpoint database")
        except Exception as e:
            logger.error(f"Error uploading databases: {e}")
    else:
        logger.info("Running locally, databases already persisted")

    logger.info("Application shutdown complete")


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="AI Task Agent",
    description="WhatsApp-based task management agent with Google Calendar integration",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
app.include_router(health.router, prefix="/health", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "running",
        "message": "AI Task Agent API",
        "version": "1.0.0",
        "environment": "cloud" if is_cloud_environment() else "local"
    }
