"""API endpoints for managing downloaded media files."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..s3 import get_presigned_url
from ..auth import require_admin
from .. import telethon_client
import datetime

router = APIRouter(prefix="/api", tags=["media"])


@router.get("/media/pending")
def list_pending_media(db: Session = Depends(get_db), _=Depends(require_admin)):
    """List media files that are pending approval."""
    items = crud.list_media(db, skip=0, limit=100, media_type=None, approved_only=False)
    pending = [m for m in items if not m.approved]
    return {"items": pending, "total": len(pending)}


@router.get("/telegram/{channel_username}/messages")
async def preview_telegram_messages(channel_username: str, limit: int = 20, _=Depends(require_admin)):
    """Preview recent media messages from a Telegram channel (metadata only)."""
    items = await telethon_client.fetch_recent_channel_messages(channel_username, limit=limit)
    return {"channel": channel_username, "items": items}


@router.get("/media/")
def list_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    media_type: str = Query(None, regex="^(audio|pdf)$"),
    approved_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List media files with pagination and filtering.
    
    Query Parameters:
        skip: Number of records to skip (pagination offset).
        limit: Max records to return (default 20, max 100).
        media_type: Filter by 'audio' or 'pdf' (optional).
        approved_only: If true, only return approved media (default false).
        
    Returns:
        dict: Contains 'items' (list of media) and 'total' (count).
    """
    total = crud.count_media(db, media_type=media_type, approved_only=approved_only)
    items = crud.list_media(
        db,
        skip=skip,
        limit=limit,
        media_type=media_type,
        approved_only=approved_only,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/media/{media_id}")
def get_media(media_id: int, db: Session = Depends(get_db)):
    """Get details of a specific media file.
    
    Args:
        media_id: Media file ID.
        db: Database session.
        
    Returns:
        MediaFile: Media file details.
        
    Raises:
        HTTPException: 404 if not found.
    """
    media = crud.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


@router.get("/media/{media_id}/download-url")
def get_download_url(
    media_id: int,
    expiration: int = Query(3600, ge=60, le=604800),
    db: Session = Depends(get_db),
):
    """Get a presigned download URL for a media file.
    
    The URL will be valid for the specified expiration time.
    
    Query Parameters:
        expiration: URL expiration time in seconds (60 to 7 days, default 1 hour).
        
    Returns:
        dict: Contains 'url' and 'expires_in'.
        
    Raises:
        HTTPException: 404 if media not found.
    """
    media = crud.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Extract bucket and object name from s3_key (format: "bucket/object")
    parts = media.s3_key.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=500, detail="Invalid S3 key format")
    
    bucket, object_name = parts

    # Only allow download URL for approved media
    if not media.approved:
        raise HTTPException(status_code=403, detail="Media is not approved for download")

    url = get_presigned_url(bucket, object_name, expiration=expiration)

    return {"url": url, "expires_in": expiration}




@router.post("/media/{media_id}/approve")
async def approve_media(media_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Mark a media file as approved.
    
    Args:
        media_id: Media file ID.
        db: Database session.
        
    Returns:
        MediaFile: Updated media file.
        
    Raises:
        HTTPException: 404 if not found.
    """
    media = crud.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Download from Telegram and upload to S3
    try:
        s3_key = await telethon_client.download_and_store_media(media.message_id, media.channel_username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download/store media: {e}")

    # Update DB record
    media.s3_key = s3_key
    media.downloaded_at = datetime.datetime.utcnow()
    media.approved = True
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.get("/media/by-channel/{channel_username}")
def get_channel_media(
    channel_username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get media files from a specific channel.
    
    Args:
        channel_username: Channel username.
        skip: Number of records to skip (pagination offset).
        limit: Max records to return.
        db: Database session.
        
    Returns:
        dict: Contains 'items' (list of media) and 'total' (count).
    """
    items = crud.get_media_by_channel(
        db, channel_username=channel_username, skip=skip, limit=limit
    )
    
    # Count total for this channel (without limit)
    total = len(
        crud.get_media_by_channel(db, channel_username=channel_username, skip=0, limit=999999)
    )
    
    return {"items": items, "total": total, "channel": channel_username}
