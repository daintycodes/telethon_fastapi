"""Telethon client for listening to Telegram channel messages."""

import os
import logging
from telethon import TelegramClient, events

from .config import API_ID, API_HASH, SESSION_NAME
from .crud import media_exists, save_media
from .s3 import store_media
from .database import SessionLocal

logger = logging.getLogger(__name__)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
_handlers_registered = False


async def start_client():
    """Start Telethon client and register event handlers (once per process)."""
    global _handlers_registered
    
    await client.start()
    
    if not _handlers_registered:
        register_handlers()
        _handlers_registered = True
    
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

                # Download and store if not already in DB
                if media_type:
                    # Use a fresh DB session for this task
                    db = SessionLocal()
                    try:
                        if not media_exists(db, msg.id):
                            # Download media from Telegram
                            file_path = await msg.download_media()
                            if file_path:
                                # Read file and upload to S3
                                with open(file_path, "rb") as f:
                                    file_data = f.read()
                                
                                s3_key = await store_media(
                                    file_data,
                                    os.path.basename(file_path),
                                    media_type
                                )
                                
                                # Save metadata to DB
                                save_media(
                                    db,
                                    message_id=msg.id,
                                    channel_username=channel.username or str(channel.id),
                                    file_name=os.path.basename(file_path),
                                    file_type=media_type,
                                    s3_key=s3_key,
                                )
                                logger.info(
                                    f"Saved media: {media_type} from {channel.username} "
                                    f"-> {s3_key}"
                                )
                                
                                # Clean up downloaded file
                                try:
                                    os.remove(file_path)
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.error(f"Error processing message {msg.id}: {e}")
                    finally:
                        db.close()
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
