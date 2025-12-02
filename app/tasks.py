"""Background task scheduling for Telethon client."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .telethon_client import start_client

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_background_tasks():
    """Start background scheduler for Telethon client.
    
    The scheduler will ensure the Telethon client is running
    and periodically checks/restarts it if needed.
    """
    # Schedule the client start check every 5 minutes
    # (not every 1 minute to avoid excessive restarts)
    scheduler.add_job(start_client, "interval", minutes=5)
    scheduler.start()
    logger.info("Background task scheduler started")
