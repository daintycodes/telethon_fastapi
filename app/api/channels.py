"""API endpoints for managing Telegram channels."""

import asyncio
import logging
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import crud, models
from ..database import get_db
from ..auth import require_admin
from ..telethon_client import pull_all_channel_media

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["channels"])


class ChannelCreate(BaseModel):
    username: str


class ChannelUpdate(BaseModel):
    active: bool


@router.post("/channels/")
def add_channel(payload: ChannelCreate = Body(...), db: Session = Depends(get_db), _=Depends(require_admin)):
    """Add a new Telegram channel to monitor.
    
    Accepts JSON body: {"username": "@channel"}
    Returns the created Channel object.
    Triggers an async media pull for this channel.
    """
    username = payload.username
    channel = models.Channel(username=username)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    # Trigger background media pull for this new channel
    try:
        asyncio.create_task(pull_all_channel_media())
        logger.info(f"Triggered media pull for new channel: {username}")
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
def toggle_channel(channel_id: int, payload: ChannelUpdate = Body(...), db: Session = Depends(get_db), _=Depends(require_admin)):
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
            asyncio.create_task(pull_all_channel_media())
            logger.info(f"Channel {channel.username} reactivated, triggering media pull")
        except Exception as e:
            logger.error(f"Failed to trigger media pull for {channel.username}: {e}")
    
    return channel
