"""CRUD operations for database models."""

from typing import Optional
from sqlalchemy.orm import Session
from . import models


def get_active_channels(db: Session):
    """Get all active channels.
    
    Args:
        db: Database session.
        
    Returns:
        list[Channel]: List of active channels.
    """
    return db.query(models.Channel).filter(models.Channel.active == True).all()


def get_channel_by_username(db: Session, username: str) -> Optional[models.Channel]:
    """Get a channel by username.
    
    Args:
        db: Database session.
        username: Channel username.
        
    Returns:
        Channel or None if not found.
    """
    return db.query(models.Channel).filter(
        models.Channel.username == username
    ).first()


def media_exists(db: Session, message_id: int) -> bool:
    """Check if media with given message_id exists.
    
    Args:
        db: Database session.
        message_id: Telegram message ID.
        
    Returns:
        bool: True if media exists.
    """
    return db.query(models.MediaFile).filter(
        models.MediaFile.message_id == message_id
    ).first() is not None


def save_media(db: Session, **kwargs) -> models.MediaFile:
    """Create and save a new MediaFile record.
    
    Args:
        db: Database session.
        **kwargs: MediaFile attributes (message_id, channel_username, etc.).
        
    Returns:
        MediaFile: Created media file record.
    """
    media = models.MediaFile(**kwargs)
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def get_media_by_id(db: Session, media_id: int) -> Optional[models.MediaFile]:
    """Get media file by ID.
    
    Args:
        db: Database session.
        media_id: Media file ID.
        
    Returns:
        MediaFile or None if not found.
    """
    return db.query(models.MediaFile).filter(
        models.MediaFile.id == media_id
    ).first()


def list_media(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    media_type: Optional[str] = None,
    approved_only: bool = False
) -> list[models.MediaFile]:
    """List media files with optional filtering and pagination.
    
    Args:
        db: Database session.
        skip: Number of records to skip (for pagination).
        limit: Maximum records to return (default 20).
        media_type: Filter by type ('audio' or 'pdf'), or None for all.
        approved_only: If True, only return approved media.
        
    Returns:
        list[MediaFile]: Matching media files.
    """
    query = db.query(models.MediaFile)
    
    if approved_only:
        query = query.filter(models.MediaFile.approved == True)
    
    if media_type:
        query = query.filter(models.MediaFile.file_type == media_type)
    
    return query.order_by(models.MediaFile.downloaded_at.desc()).offset(
        skip
    ).limit(limit).all()


def get_media_by_channel(
    db: Session,
    channel_username: str,
    skip: int = 0,
    limit: int = 20
) -> list[models.MediaFile]:
    """Get media files from a specific channel.
    
    Args:
        db: Database session.
        channel_username: Channel username.
        skip: Number of records to skip (for pagination).
        limit: Maximum records to return.
        
    Returns:
        list[MediaFile]: Media files from the channel.
    """
    return db.query(models.MediaFile).filter(
        models.MediaFile.channel_username == channel_username
    ).order_by(
        models.MediaFile.downloaded_at.desc()
    ).offset(skip).limit(limit).all()


def approve_media(db: Session, media_id: int) -> Optional[models.MediaFile]:
    """Mark a media file as approved.
    
    Args:
        db: Database session.
        media_id: Media file ID.
        
    Returns:
        MediaFile or None if not found.
    """
    media = db.query(models.MediaFile).filter(
        models.MediaFile.id == media_id
    ).first()
    
    if media:
        media.approved = True
        db.commit()
        db.refresh(media)
    
    return media


def count_media(
    db: Session,
    media_type: Optional[str] = None,
    approved_only: bool = False
) -> int:
    """Count media files with optional filtering.
    
    Args:
        db: Database session.
        media_type: Filter by type.
        approved_only: If True, only count approved media.
        
    Returns:
        int: Count of matching media files.
    """
    query = db.query(models.MediaFile)
    
    if approved_only:
        query = query.filter(models.MediaFile.approved == True)
    
    if media_type:
        query = query.filter(models.MediaFile.file_type == media_type)
    
    return query.count()
