"""FastAPI application initialization and startup/shutdown logic."""

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .database import engine, SessionLocal
from .models import Base
from .api import channels, media
from .tasks import start_background_tasks, scheduler
from .s3 import ensure_buckets_exist
from .telethon_client import start_client

logger = logging.getLogger(__name__)


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
