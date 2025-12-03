"""Background task scheduling for Telethon client."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .telethon_client import client, _client_started, start_client

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_and_reconnect_client():
    """Check Telethon client connection and reconnect if needed."""
    from .telethon_client import _client_started
    
    try:
        if not _client_started:
            logger.warning("Telethon client not started, attempting to start...")
            await start_client()
        elif not client.is_connected():
            logger.warning("Telethon client disconnected, attempting to reconnect...")
            await client.connect()
            if client.is_connected():
                logger.info("Telethon client reconnected successfully")
            else:
                logger.error("Failed to reconnect Telethon client")
                # Try full restart
                await start_client()
        else:
            logger.debug("Telethon client connection check: OK")
    except Exception as e:
        logger.error(f"Error checking/reconnecting Telethon client: {e}", exc_info=True)


def start_background_tasks():
    """Start background scheduler for Telethon client.
    
    The scheduler will ensure the Telethon client is running
    and periodically checks/restarts it if needed.
    """
    # Schedule the client connection check every 5 minutes
    # This will reconnect if disconnected
    scheduler.add_job(check_and_reconnect_client, "interval", minutes=5)
    scheduler.start()
    logger.info("Background task scheduler started (checking Telethon connection every 5 minutes)")
