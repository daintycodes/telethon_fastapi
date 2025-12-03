"""Diagnostic and manual trigger endpoints for troubleshooting."""

import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import require_admin
from ..telethon_client import client, _client_started, pull_all_channel_media
from .. import crud, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("/status")
async def get_system_status(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Get comprehensive system status for diagnostics."""
    
    # Telethon status
    is_user = None
    is_bot = None
    if _client_started and client.is_connected():
        try:
            is_user = await client.is_user()
            is_bot = await client.is_bot()
        except Exception as e:
            logger.warning(f"Could not determine client type: {e}")
    
    telethon_status = {
        "started": _client_started,
        "connected": client.is_connected() if _client_started else False,
        "is_user": is_user,
        "is_bot": is_bot,
    }
    
    # Database status
    try:
        total_channels = db.query(models.Channel).count()
        active_channels = db.query(models.Channel).filter(models.Channel.active == True).count()
        total_media = db.query(models.MediaFile).count()
        pending_media = db.query(models.MediaFile).filter(models.MediaFile.approved == False).count()
        approved_media = db.query(models.MediaFile).filter(models.MediaFile.approved == True).count()
        
        db_status = {
            "connected": True,
            "total_channels": total_channels,
            "active_channels": active_channels,
            "total_media": total_media,
            "pending_media": pending_media,
            "approved_media": approved_media,
        }
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        db_status = {
            "connected": False,
            "error": str(e)
        }
    
    # Get channel list
    try:
        channels = crud.get_all_channels(db, active_only=False)
        channel_list = [
            {
                "id": c.id,
                "username": c.username,
                "active": c.active
            }
            for c in channels
        ]
    except Exception as e:
        logger.error(f"Failed to get channel list: {e}")
        channel_list = []
    
    return {
        "telethon": telethon_status,
        "database": db_status,
        "channels": channel_list,
        "recommendations": generate_recommendations(telethon_status, db_status, channel_list)
    }


def generate_recommendations(telethon_status, db_status, channel_list):
    """Generate actionable recommendations based on system status."""
    recommendations = []
    
    if not telethon_status["connected"]:
        recommendations.append({
            "severity": "critical",
            "issue": "Telethon client not connected",
            "action": "Check TG_BOT_TOKEN environment variable or session file. Restart application."
        })
    
    if db_status.get("active_channels", 0) == 0:
        recommendations.append({
            "severity": "warning",
            "issue": "No active channels configured",
            "action": "Add channels via the Channels tab to start pulling media."
        })
    
    if db_status.get("total_media", 0) == 0 and db_status.get("active_channels", 0) > 0:
        recommendations.append({
            "severity": "warning",
            "issue": "No media pulled despite having active channels",
            "action": "Use 'Trigger Media Pull' button to manually pull media from channels."
        })
    
    if db_status.get("pending_media", 0) > 0:
        recommendations.append({
            "severity": "info",
            "issue": f"{db_status['pending_media']} media files awaiting approval",
            "action": "Go to Pending Media tab to approve files for download."
        })
    
    if not recommendations:
        recommendations.append({
            "severity": "success",
            "issue": "System healthy",
            "action": "All systems operational."
        })
    
    return recommendations


@router.post("/trigger-pull")
async def trigger_media_pull(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Manually trigger media pull from all active channels."""
    
    # Check if client is connected
    if not _client_started or not client.is_connected():
        return {
            "success": False,
            "error": "Telethon client not connected",
            "message": "Cannot pull media: Telethon client is not connected. Check TG_BOT_TOKEN."
        }
    
    # Check if there are active channels
    active_channels = crud.get_all_channels(db, active_only=True)
    if not active_channels:
        return {
            "success": False,
            "error": "No active channels",
            "message": "No active channels configured. Add channels first."
        }
    
    # Trigger pull in background
    try:
        background_tasks.add_task(pull_all_channel_media)
        logger.info("Manual media pull triggered from diagnostics endpoint")
        
        return {
            "success": True,
            "message": f"Media pull triggered for {len(active_channels)} active channel(s)",
            "channels": [c.username for c in active_channels]
        }
    except Exception as e:
        logger.error(f"Failed to trigger media pull: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to trigger media pull"
        }


@router.get("/logs/recent")
async def get_recent_logs(_=Depends(require_admin)):
    """Get recent application logs (if available)."""
    # This is a placeholder - in production, you'd read from a log file or logging service
    return {
        "message": "Log viewing not implemented",
        "recommendation": "Check application logs in Coolify dashboard or container logs"
    }
