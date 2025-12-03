"""FastAPI application initialization and startup/shutdown logic."""

import logging
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .database import engine, SessionLocal
from .models import Base
from .api import channels, media
from .api.diagnostics import router as diagnostics_router
from .admin import router as admin_router
from .auth_jwt import router as auth_router
from .tasks import start_background_tasks, scheduler
from .s3 import ensure_buckets_exist
from .telethon_client import start_client
from .logging_config import configure_logging
from sentry_sdk import init as sentry_init
from .config import SENTRY_DSN

configure_logging()

logger = logging.getLogger(__name__)

# Initialize Sentry if DSN provided
if SENTRY_DSN:
    try:
        sentry_init(dsn=SENTRY_DSN, traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")))
        logger.info("Sentry initialized")
    except Exception:
        logger.exception("Failed to initialize Sentry")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown.
    
    Startup:
        - Create database tables
        - Ensure S3 buckets exist
        - Start Telethon client
        - Start background task scheduler
        
    Shutdown:
        - Shut down the scheduler
    """
    # Startup
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("Ensuring S3 buckets exist...")
        ensure_buckets_exist()
        
        logger.info("Starting Telethon client...")
        await start_client()
        
        logger.info("Starting background task scheduler...")
        start_background_tasks()
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down scheduler...")
        if scheduler.running:
            scheduler.shutdown(wait=True)
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI app with lifespan context manager
app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(channels.router)
app.include_router(media.router)
app.include_router(diagnostics_router)
app.include_router(admin_router)
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Health check endpoint with Telethon client status."""
    try:
        from .telethon_client import client, _client_started
        
        telethon_status = "disconnected"
        if _client_started and client.is_connected():
            telethon_status = "connected"
        elif _client_started:
            telethon_status = "started_but_disconnected"
        
        return {
            "status": "healthy",
            "telethon_client": telethon_status,
            "telethon_connected": client.is_connected() if _client_started else False
        }
    except Exception as e:
        # If telethon_client fails to import, still return healthy but show error
        return {
            "status": "healthy",
            "telethon_client": "import_failed",
            "telethon_connected": False,
            "telethon_error": str(e)
        }
