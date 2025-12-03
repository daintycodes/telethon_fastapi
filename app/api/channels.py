"""API endpoints for managing Telegram channels."""

import asyncio
import logging
import re
from fastapi import APIRouter, Depends, Body, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import crud, models
from ..database import get_db
from ..auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["channels"])


def validate_channel_username(username: str) -> str:
    """Validate and normalize channel username.
    
    Accepts:
    - @username
    - username
    - t.me/username
    - https://t.me/username
    
    Returns: @username (normalized)
    Raises: ValueError if invalid
    """
    if not username:
        raise ValueError("Channel username cannot be empty")
    
    original = username
    
    # Remove URL prefixes
    username = username.replace("https://t.me/", "")
    username = username.replace("http://t.me/", "")
    username = username.replace("t.me/", "")
    username = username.strip()
    
    # Add @ prefix if missing
    if not username.startswith("@"):
        username = f"@{username}"
    
    # Validate format: @username (alphanumeric + underscore, 5-32 chars)
    if not re.match(r"^@[a-zA-Z0-9_]{5,32}$", username):
        raise ValueError(
            f"Invalid channel username format: '{original}'. "
            f"Must be 5-32 characters, alphanumeric and underscores only. "
            f"Normalized to: '{username}'"
        )
    
    return username


class ChannelCreate(BaseModel):
    username: str


class ChannelUpdate(BaseModel):
    active: bool


@router.post("/channels/")
async def add_channel(
    payload: ChannelCreate = Body(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Add a new Telegram channel to monitor.
    
    Accepts JSON body: {"username": "@channel"}
    Returns the created Channel object.
    Triggers an async media pull for this channel.
    """
    # Validate and normalize username
    try:
        normalized_username = validate_channel_username(payload.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check for duplicates
    existing = db.query(models.Channel).filter(
        models.Channel.username == normalized_username
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Channel {normalized_username} already exists with ID {existing.id}"
        )
    
    username = normalized_username
    channel = models.Channel(username=username)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    # Trigger background media pull for this new channel
    try:
        from ..telethon_client import pull_all_channel_media
        
        if background_tasks:
            background_tasks.add_task(pull_all_channel_media)
        else:
            # Fallback: create task with proper reference
            task = asyncio.create_task(pull_all_channel_media())
            # Store reference to prevent garbage collection
            asyncio.ensure_future(task)
        logger.info(f"Triggered media pull for new channel: {username}")
    except ImportError as ie:
        logger.error(f"Cannot import telethon_client: {ie}")
    except Exception as e:
        logger.error(f"Failed to trigger media pull for {username}: {e}")
    
    return channel


@router.get("/channels/")
def list_channels(db: Session = Depends(get_db)):
    """List all active Telegram channels being monitored.
    
    Args:
        db: Database session.
        
    Returns:
        list[Channel]: List of active channels.
    """
    return crud.get_active_channels(db)

@router.get("/channels/all")
def list_all_channels(db: Session = Depends(get_db), _=Depends(require_admin)):
    """List all channels including inactive ones."""
    return db.query(models.Channel).order_by(models.Channel.id.asc()).all()

@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Delete (or deactivate) a channel by ID."""
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Channel not found")
    # Soft-delete: mark as inactive
    channel.active = False
    db.commit()
    db.refresh(channel)
    return {"status": "deactivated", "id": channel_id}

@router.patch("/channels/{channel_id}")
async def toggle_channel(
    channel_id: int,
    payload: ChannelUpdate = Body(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Set channel active/inactive state.
    
    Accepts JSON body: {"active": true/false}
    If channel is being activated, triggers media pull in background.
    """
    from fastapi import HTTPException
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    was_inactive = not channel.active
    channel.active = payload.active
    db.commit()
    db.refresh(channel)
    
    # If reactivating, trigger media pull
    if was_inactive and channel.active:
        try:
            from ..telethon_client import pull_all_channel_media
            
            if background_tasks:
                background_tasks.add_task(pull_all_channel_media)
            else:
                # Fallback: create task with proper reference
                task = asyncio.create_task(pull_all_channel_media())
                asyncio.ensure_future(task)
            logger.info(f"Channel {channel.username} reactivated, triggering media pull")
        except ImportError as ie:
            logger.error(f"Cannot import telethon_client: {ie}")
        except Exception as e:
            logger.error(f"Failed to trigger media pull for {channel.username}: {e}")
    
    return channel
