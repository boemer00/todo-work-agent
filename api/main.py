"""FastAPI application for WhatsApp integration."""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable LangSmith tracing for observability
from monitoring import setup_langsmith
setup_langsmith()

from fastapi import FastAPI, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient

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

# Initialize Redis for rate limiting (with graceful fallback)
redis_client = None
storage_uri = "memory://"  # Default to in-memory for development

if os.getenv("REDIS_URL"):
    try:
        redis_client = redis.from_url(
            os.getenv("REDIS_URL"),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        # Test connection
        redis_client.ping()
        storage_uri = os.getenv("REDIS_URL")
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Rate limiting will use in-memory storage.")
        redis_client = None
        storage_uri = "memory://"
else:
    logger.warning("REDIS_URL not set. Rate limiting will use in-memory storage (not recommended for production).")

# Initialize SlowAPI rate limiter
limiter = Limiter(
    key_func=get_remote_address,  # Default key function (can be overridden per route)
    storage_uri=storage_uri,
    default_limits=[]  # No global limits, only per-route limits
)


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

# Add rate limiter and Redis client to app state
app.state.limiter = limiter
app.state.redis_client = redis_client  # Expose Redis client for manual rate limiting

# Initialize Twilio client for sending messages programmatically
try:
    app.state.twilio_client = TwilioClient(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    logger.info("Twilio client initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Twilio client: {e}")
    app.state.twilio_client = None

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handle rate limit errors with user-friendly TwiML response.

    Returns 429 status with Retry-After header for Twilio.
    """
    logger.warning(f"Rate limit exceeded for {request.url}")

    # Create Twilio-compatible response
    response_obj = MessagingResponse()
    response_obj.message(
        "⏱️ You're sending messages too quickly. "
        "Please wait a moment and try again."
    )

    return Response(
        content=str(response_obj),
        status_code=429,
        media_type="application/xml",
        headers={"Retry-After": "60"}
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
