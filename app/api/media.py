"""API endpoints for managing downloaded media files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from .. import crud
from ..database import get_db
from ..s3 import get_presigned_url
from ..auth import require_admin
from .. import telethon_client
import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["media"])


@router.get("/media/pending")
def list_pending_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """List media files that are pending approval with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default 0).
        limit: Max records to return (default 100, max 1000).
    """
    items = crud.list_media(db, skip=skip, limit=limit, media_type=None, approved_only=False)
    pending = [m for m in items if not m.approved]
    total_pending = crud.count_media(db, media_type=None, approved_only=False)
    return {"items": pending, "total": total_pending, "skip": skip, "limit": limit}


@router.get("/telegram/{channel_username}/messages")
async def preview_telegram_messages(channel_username: str, limit: int = 20, _=Depends(require_admin)):
    """Preview recent media messages from a Telegram channel (metadata only)."""
    items = await telethon_client.fetch_recent_channel_messages(channel_username, limit=limit)
    return {"channel": channel_username, "items": items}


@router.get("/media/")
def list_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    media_type: str = Query(None, regex="^(audio|pdf)$"),
    approved_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List media files with pagination and filtering.
    
    Query Parameters:
        skip: Number of records to skip (pagination offset).
        limit: Max records to return (default 100, max 1000).
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


class BatchApprovalRequest(BaseModel):
    """Request model for batch approval."""
    media_ids: List[int]


@router.post("/media/batch-approve")
async def batch_approve_media(
    request: BatchApprovalRequest,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Approve multiple media files in batch.
    
    Args:
        request: Contains list of media IDs to approve.
        db: Database session.
        
    Returns:
        dict: Summary of successful and failed approvals.
    """
    if not request.media_ids:
        raise HTTPException(status_code=400, detail="No media IDs provided")
    
    if len(request.media_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 media files can be approved at once")
    
    successful = []
    failed = []
    
    for media_id in request.media_ids:
        try:
            media = crud.get_media_by_id(db, media_id)
            if not media:
                failed.append({"id": media_id, "error": "Media not found"})
                continue
            
            # Skip if already approved
            if media.approved:
                successful.append({"id": media_id, "status": "already_approved", "filename": media.filename})
                continue
            
            # Download from Telegram and upload to S3
            try:
                s3_key = await telethon_client.download_and_store_media(media.message_id, media.channel_username)
            except Exception as download_error:
                failed.append({"id": media_id, "error": str(download_error), "filename": media.filename})
                logger.error(f"Failed to download media {media_id}: {download_error}")
                continue
            
            # Update DB record
            media.s3_key = s3_key
            media.downloaded_at = datetime.datetime.utcnow()
            media.approved = True
            db.add(media)
            db.commit()
            
            successful.append({"id": media_id, "status": "approved", "filename": media.filename})
            logger.info(f"Successfully approved media {media_id}: {media.filename}")
            
        except Exception as e:
            failed.append({"id": media_id, "error": str(e)})
            logger.error(f"Unexpected error approving media {media_id}: {e}")
            # Rollback this transaction
            db.rollback()
    
    return {
        "total": len(request.media_ids),
        "successful": len(successful),
        "failed": len(failed),
        "successful_items": successful,
        "failed_items": failed
    }


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
