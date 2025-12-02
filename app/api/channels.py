"""API endpoints for managing Telegram channels."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import get_db

router = APIRouter(prefix="/api", tags=["channels"])


@router.post("/channels/")
def add_channel(username: str, db: Session = Depends(get_db)):
    """Add a new Telegram channel to monitor.
    
    Args:
        username: Telegram channel username.
        db: Database session.
        
    Returns:
        Channel: Created channel object.
    """
    channel = models.Channel(username=username)
    db.add(channel)
    db.commit()
    db.refresh(channel)
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
def list_all_channels(db: Session = Depends(get_db)):
    """List all channels including inactive ones."""
    return db.query(models.Channel).order_by(models.Channel.id.asc()).all()

@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
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
def toggle_channel(channel_id: int, active: bool, db: Session = Depends(get_db)):
    """Set channel active/inactive state."""
    from fastapi import HTTPException
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel.active = bool(active)
    db.commit()
    db.refresh(channel)
    return channel
