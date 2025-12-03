"""Telethon client for listening to Telegram channel messages."""

import os
import logging
from telethon import TelegramClient, events

from .config import API_ID, API_HASH, SESSION_NAME
from .crud import media_exists, save_media
from .s3 import store_media
from .database import SessionLocal

import logging
import os

logger = logging.getLogger(__name__)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
_handlers_registered = False


async def start_client():
    """Start Telethon client, pull historical media, and register event handlers (once per process)."""
    global _handlers_registered
    
    # Avoid interactive prompts in non-interactive containers.
    # If a bot token is provided via env var `TG_BOT_TOKEN` (or `TELEGRAM_BOT_TOKEN`), use it.
    # Otherwise only start if an existing session file exists to prevent Telethon from calling input().
    bot_token = os.getenv("TG_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    session_file = f"{SESSION_NAME}.session"

    if bot_token:
        await client.start(bot_token=bot_token)
    else:
        if os.path.exists(session_file):
            await client.start()
        else:
            logger.error(
                "No TG_BOT_TOKEN and no existing Telethon session file found. "
                "Skipping Telethon client start to avoid interactive prompt. "
                "Provide a bot token via TG_BOT_TOKEN or mount a session file."
            )
            return
    
    if not _handlers_registered:
        register_handlers()
        _handlers_registered = True
        
        # Pull all historical audio/pdf messages from all active channels
        await pull_all_channel_media()
    
    logger.info("Telethon client started and handlers registered")


def register_handlers():
    """Register NewMessage event handler for downloading media."""
    
    @client.on(events.NewMessage)
    async def handler(event):
        try:
            channel = await event.get_chat()
            msg = event.message
            media_type = None

            if msg.file:
                # Determine media type from MIME type
                if msg.file.mime_type in ["audio/mpeg", "audio/ogg"]:
                    media_type = "audio"
                elif msg.file.mime_type == "application/pdf":
                    media_type = "pdf"

                # Record pending media metadata (do not download automatically)
                if media_type:
                    # Use a fresh DB session for this task
                    db = SessionLocal()
                    try:
                        if not media_exists(db, msg.id):
                            # Do NOT download immediately. Save a pending record
                            # so an admin can review and approve before download.
                            suggested_name = getattr(msg.file, "name", None)
                            save_media(
                                db,
                                message_id=msg.id,
                                channel_username=channel.username or str(channel.id),
                                file_name=suggested_name or f"message_{msg.id}",
                                file_type=media_type,
                                s3_key=None,
                            )
                            logger.info(f"Recorded pending media message {msg.id} from {channel.username}")
                    except Exception as e:
                        logger.error(f"Error recording message {msg.id}: {e}")
                    finally:
                        db.close()
        except Exception as e:
            logger.error(f"Error in message handler: {e}")


async def pull_all_channel_media():
    """Pull all historical audio and PDF messages from all active channels on startup."""
    from .crud import get_all_channels
    
    logger.info("Starting historical media pull from all active channels...")
    db = SessionLocal()
    try:
        channels = get_all_channels(db, active_only=True)
        for channel in channels:
            # Channel model uses `username` field
            logger.info(f"Pulling historical media from channel: {channel.username}")
            try:
                entity = await client.get_entity(channel.username)
                # Fetch ALL messages from this channel (no limit)
                messages = await client.get_messages(entity, limit=None)
                
                media_count = 0
                for msg in messages:
                    if msg.file:
                        media_type = None
                        if msg.file.mime_type in ["audio/mpeg", "audio/ogg"]:
                            media_type = "audio"
                        elif msg.file.mime_type == "application/pdf":
                            media_type = "pdf"
                        
                        if media_type and not media_exists(db, msg.id):
                            suggested_name = getattr(msg.file, "name", None)
                            save_media(
                                db,
                                message_id=msg.id,
                                channel_username=channel.username,
                                file_name=suggested_name or f"message_{msg.id}",
                                file_type=media_type,
                                s3_key=None,
                            )
                            media_count += 1
                
                logger.info(f"Pulled {media_count} audio/PDF messages from {channel.username}")
            except Exception as e:
                logger.error(f"Error pulling media from {channel.username}: {e}")
    finally:
        db.close()
    
    logger.info("Historical media pull completed")


async def fetch_recent_channel_messages(channel_username: str, limit: int = 20):
    """Fetch recent messages from a Telegram channel (returns metadata only).

    Returns a list of dicts with message_id, date, file_name, mime_type, file_size, and text.
    """
    result = []
    try:
        entity = await client.get_entity(channel_username)
        messages = await client.get_messages(entity, limit=limit)
        for m in messages:
            if m.file:
                result.append(
                    {
                        "message_id": m.id,
                        "date": m.date.isoformat() if m.date else None,
                        "file_name": getattr(m.file, "name", None),
                        "mime_type": getattr(m.file, "mime_type", None),
                        "file_size": getattr(m.file, "size", None),
                        "text": m.text,
                    }
                )
    except Exception as e:
        logger.error(f"Failed to fetch messages for {channel_username}: {e}")
    return result


async def download_and_store_media(message_id: int, channel_username: str = None):
    """Download a media message by ID and upload to S3. Returns s3_key or raises."""
    # Fetch the message either by id and channel or search recent
    try:
        if channel_username:
            entity = await client.get_entity(channel_username)
            msg = await client.get_messages(entity, ids=message_id)
        else:
            # try to fetch globally by id
            msg = await client.get_messages(message_id)

        if not msg or not msg.file:
            raise RuntimeError("Message not found or has no file")

        # Download to temp file
        file_path = await msg.download_media()
        if not file_path:
            raise RuntimeError("Failed to download media")

        # Read and upload
        with open(file_path, "rb") as f:
            data = f.read()

        media_type = None
        if msg.file.mime_type in ["audio/mpeg", "audio/ogg"]:
            media_type = "audio"
        elif msg.file.mime_type == "application/pdf":
            media_type = "pdf"

        if not media_type:
            raise RuntimeError("Unsupported media type")

        s3_key = await store_media(data, os.path.basename(file_path), media_type)

        # Clean up
        try:
            os.remove(file_path)
        except Exception:
            pass

        return s3_key
    except Exception as e:
        logger.error(f"download_and_store_media failed for {message_id}: {e}")
        raise