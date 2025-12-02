"""Tests for API endpoints."""

import json
import pytest
from app import models


class TestChannelEndpoints:
    """Test channel API endpoints."""
    
    def test_add_channel(self, test_client, test_db):
        """Test adding a new channel."""
        response = test_client.post("/api/channels/?username=testchannel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testchannel"
        assert data["active"] is True
        assert "id" in data
    
    def test_list_channels(self, test_client, test_db):
        """Test listing channels."""
        # Add test data
        test_db.add(models.Channel(username="channel1", active=True))
        test_db.add(models.Channel(username="channel2", active=True))
        test_db.add(models.Channel(username="channel3", active=False))
        test_db.commit()
        
        response = test_client.get("/api/channels/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only active channels
        usernames = {ch["username"] for ch in data}
        assert usernames == {"channel1", "channel2"}
    
    def test_list_channels_empty(self, test_client):
        """Test listing channels when empty."""
        response = test_client.get("/api/channels/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestMediaEndpoints:
    """Test media API endpoints."""
    
    def test_list_media_empty(self, test_client):
        """Test listing media when no files exist."""
        response = test_client.get("/api/media/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
    
    def test_list_media_with_pagination(self, test_client, test_db):
        """Test listing media with pagination."""
        # Add test data
        for i in range(35):
            test_db.add(
                models.MediaFile(
                    message_id=1000 + i,
                    channel_username="testchannel",
                    file_name=f"file{i}.mp3",
                    file_type="audio",
                    s3_key=f"audio/file{i}-uuid.mp3",
                )
            )
        test_db.commit()
        
        # First page
        response = test_client.get("/api/media/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 35
        assert len(data["items"]) == 10
        assert data["skip"] == 0
        assert data["limit"] == 10
        
        # Second page
        response = test_client.get("/api/media/?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
    
    def test_list_media_by_type(self, test_client, test_db):
        """Test filtering media by type."""
        test_db.add(
            models.MediaFile(
                message_id=2000,
                channel_username="testchannel",
                file_name="song.mp3",
                file_type="audio",
                s3_key="audio/song.mp3",
            )
        )
        test_db.add(
            models.MediaFile(
                message_id=2001,
                channel_username="testchannel",
                file_name="doc.pdf",
                file_type="pdf",
                s3_key="pdf/doc.pdf",
            )
        )
        test_db.commit()
        
        response = test_client.get("/api/media/?media_type=audio")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["file_type"] == "audio"
    
    def test_list_media_approved_only(self, test_client, test_db):
        """Test filtering approved media."""
        test_db.add(
            models.MediaFile(
                message_id=3000,
                channel_username="testchannel",
                file_name="approved.mp3",
                file_type="audio",
                s3_key="audio/approved.mp3",
                approved=True,
            )
        )
        test_db.add(
            models.MediaFile(
                message_id=3001,
                channel_username="testchannel",
                file_name="pending.mp3",
                file_type="audio",
                s3_key="audio/pending.mp3",
                approved=False,
            )
        )
        test_db.commit()
        
        response = test_client.get("/api/media/?approved_only=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["approved"] is True
    
    def test_get_media_by_id(self, test_client, test_db):
        """Test getting media by ID."""
        media = models.MediaFile(
            message_id=4000,
            channel_username="testchannel",
            file_name="test.mp3",
            file_type="audio",
            s3_key="audio/test.mp3",
        )
        test_db.add(media)
        test_db.commit()
        
        response = test_client.get(f"/api/media/{media.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "test.mp3"
        assert data["message_id"] == 4000
    
    def test_get_media_by_id_not_found(self, test_client):
        """Test getting non-existent media."""
        response = test_client.get("/api/media/99999")
        assert response.status_code == 404
    
    def test_approve_media(self, test_client, test_db):
        """Test approving media."""
        media = models.MediaFile(
            message_id=5000,
            channel_username="testchannel",
            file_name="unapproved.mp3",
            file_type="audio",
            s3_key="audio/unapproved.mp3",
            approved=False,
        )
        test_db.add(media)
        test_db.commit()
        
        response = test_client.post(f"/api/media/{media.id}/approve")
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is True
    
    def test_approve_media_not_found(self, test_client):
        """Test approving non-existent media."""
        response = test_client.post("/api/media/99999/approve")
        assert response.status_code == 404
    
    def test_get_channel_media(self, test_client, test_db):
        """Test getting media by channel."""
        for i in range(3):
            test_db.add(
                models.MediaFile(
                    message_id=6000 + i,
                    channel_username="channel1",
                    file_name=f"file{i}.mp3",
                    file_type="audio",
                    s3_key=f"audio/file{i}.mp3",
                )
            )
        test_db.add(
            models.MediaFile(
                message_id=6100,
                channel_username="channel2",
                file_name="other.mp3",
                file_type="audio",
                s3_key="audio/other.mp3",
            )
        )
        test_db.commit()
        
        response = test_client.get("/api/media/by-channel/channel1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert all(m["channel_username"] == "channel1" for m in data["items"])
    
    def test_get_channel_media_empty(self, test_client):
        """Test getting media for non-existent channel."""
        response = test_client.get("/api/media/by-channel/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
    
    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDownloadURL:
    """Test presigned download URL endpoint."""
    
    def test_get_download_url_not_found(self, test_client):
        """Test getting download URL for non-existent media."""
        response = test_client.get("/api/media/99999/download-url")
        assert response.status_code == 404
    
    def test_get_download_url_invalid_expiration(self, test_client, test_db):
        """Test invalid expiration parameter."""
        media = models.MediaFile(
            message_id=7000,
            channel_username="testchannel",
            file_name="test.mp3",
            file_type="audio",
            s3_key="audio/test.mp3",
        )
        test_db.add(media)
        test_db.commit()
        
        # Too short (less than 60 seconds)
        response = test_client.get(f"/api/media/{media.id}/download-url?expiration=30")
        assert response.status_code == 422  # Validation error
        
        # Too long (more than 7 days)
        response = test_client.get(f"/api/media/{media.id}/download-url?expiration=999999")
        assert response.status_code == 422
