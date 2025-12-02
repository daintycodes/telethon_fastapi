"""Tests for CRUD operations."""

import pytest
from app import models, crud


class TestChannelCRUD:
    """Test Channel model CRUD operations."""
    
    def test_get_active_channels(self, test_db):
        """Test retrieving active channels."""
        # Create test channels
        ch1 = models.Channel(username="channel1", active=True)
        ch2 = models.Channel(username="channel2", active=True)
        ch3 = models.Channel(username="channel3", active=False)
        
        test_db.add_all([ch1, ch2, ch3])
        test_db.commit()
        
        # Query active channels
        active = crud.get_active_channels(test_db)
        assert len(active) == 2
        assert all(ch.active for ch in active)
        usernames = {ch.username for ch in active}
        assert usernames == {"channel1", "channel2"}
    
    def test_get_channel_by_username(self, test_db):
        """Test retrieving channel by username."""
        channel = models.Channel(username="testchannel", active=True)
        test_db.add(channel)
        test_db.commit()
        
        result = crud.get_channel_by_username(test_db, "testchannel")
        assert result is not None
        assert result.username == "testchannel"
        assert result.active is True
    
    def test_get_channel_by_username_not_found(self, test_db):
        """Test retrieving non-existent channel."""
        result = crud.get_channel_by_username(test_db, "nonexistent")
        assert result is None


class TestMediaFileCRUD:
    """Test MediaFile model CRUD operations."""
    
    def test_media_exists(self, test_db):
        """Test checking if media exists."""
        media = models.MediaFile(
            message_id=123,
            channel_username="testchannel",
            file_name="test.mp3",
            file_type="audio",
            s3_key="audio/test-uuid.mp3",
        )
        test_db.add(media)
        test_db.commit()
        
        assert crud.media_exists(test_db, 123) is True
        assert crud.media_exists(test_db, 999) is False
    
    def test_save_media(self, test_db):
        """Test creating and saving media."""
        media = crud.save_media(
            test_db,
            message_id=456,
            channel_username="testchannel",
            file_name="document.pdf",
            file_type="pdf",
            s3_key="pdf/doc-uuid.pdf",
        )
        
        assert media.id is not None
        assert media.message_id == 456
        assert media.file_type == "pdf"
        assert media.approved is False
    
    def test_get_media_by_id(self, test_db):
        """Test retrieving media by ID."""
        media = models.MediaFile(
            message_id=789,
            channel_username="testchannel",
            file_name="audio.ogg",
            file_type="audio",
            s3_key="audio/audio-uuid.ogg",
        )
        test_db.add(media)
        test_db.commit()
        
        retrieved = crud.get_media_by_id(test_db, media.id)
        assert retrieved is not None
        assert retrieved.file_name == "audio.ogg"
    
    def test_list_media_pagination(self, test_db):
        """Test listing media with pagination."""
        # Create multiple media files
        for i in range(25):
            media = models.MediaFile(
                message_id=1000 + i,
                channel_username="testchannel",
                file_name=f"file{i}.mp3",
                file_type="audio",
                s3_key=f"audio/file{i}.mp3",
            )
            test_db.add(media)
        test_db.commit()
        
        # First page
        page1 = crud.list_media(test_db, skip=0, limit=10)
        assert len(page1) == 10
        
        # Second page
        page2 = crud.list_media(test_db, skip=10, limit=10)
        assert len(page2) == 10
        
        # Third page (partial)
        page3 = crud.list_media(test_db, skip=20, limit=10)
        assert len(page3) == 5
    
    def test_list_media_by_type(self, test_db):
        """Test filtering media by type."""
        audio = models.MediaFile(
            message_id=2000,
            channel_username="testchannel",
            file_name="song.mp3",
            file_type="audio",
            s3_key="audio/song.mp3",
        )
        pdf = models.MediaFile(
            message_id=2001,
            channel_username="testchannel",
            file_name="book.pdf",
            file_type="pdf",
            s3_key="pdf/book.pdf",
        )
        test_db.add_all([audio, pdf])
        test_db.commit()
        
        audio_files = crud.list_media(test_db, media_type="audio")
        assert len(audio_files) == 1
        assert audio_files[0].file_type == "audio"
        
        pdf_files = crud.list_media(test_db, media_type="pdf")
        assert len(pdf_files) == 1
        assert pdf_files[0].file_type == "pdf"
    
    def test_list_media_approved_only(self, test_db):
        """Test filtering approved media."""
        media1 = models.MediaFile(
            message_id=3000,
            channel_username="testchannel",
            file_name="file1.mp3",
            file_type="audio",
            s3_key="audio/file1.mp3",
            approved=True,
        )
        media2 = models.MediaFile(
            message_id=3001,
            channel_username="testchannel",
            file_name="file2.mp3",
            file_type="audio",
            s3_key="audio/file2.mp3",
            approved=False,
        )
        test_db.add_all([media1, media2])
        test_db.commit()
        
        approved = crud.list_media(test_db, approved_only=True)
        assert len(approved) == 1
        assert approved[0].approved is True
    
    def test_get_media_by_channel(self, test_db):
        """Test retrieving media by channel."""
        ch1_media1 = models.MediaFile(
            message_id=4000,
            channel_username="channel1",
            file_name="file1.mp3",
            file_type="audio",
            s3_key="audio/file1.mp3",
        )
        ch1_media2 = models.MediaFile(
            message_id=4001,
            channel_username="channel1",
            file_name="file2.mp3",
            file_type="audio",
            s3_key="audio/file2.mp3",
        )
        ch2_media = models.MediaFile(
            message_id=4002,
            channel_username="channel2",
            file_name="file3.mp3",
            file_type="audio",
            s3_key="audio/file3.mp3",
        )
        test_db.add_all([ch1_media1, ch1_media2, ch2_media])
        test_db.commit()
        
        ch1_files = crud.get_media_by_channel(test_db, "channel1")
        assert len(ch1_files) == 2
        assert all(m.channel_username == "channel1" for m in ch1_files)
    
    def test_approve_media(self, test_db):
        """Test approving media."""
        media = models.MediaFile(
            message_id=5000,
            channel_username="testchannel",
            file_name="file.mp3",
            file_type="audio",
            s3_key="audio/file.mp3",
            approved=False,
        )
        test_db.add(media)
        test_db.commit()
        
        updated = crud.approve_media(test_db, media.id)
        assert updated.approved is True
        
        # Verify in DB
        recheck = test_db.query(models.MediaFile).filter(
            models.MediaFile.id == media.id
        ).first()
        assert recheck.approved is True
    
    def test_count_media(self, test_db):
        """Test counting media."""
        # Add mixed media
        for i in range(5):
            test_db.add(
                models.MediaFile(
                    message_id=6000 + i,
                    channel_username="testchannel",
                    file_name=f"file{i}.mp3",
                    file_type="audio",
                    s3_key=f"audio/file{i}.mp3",
                    approved=(i % 2 == 0),
                )
            )
        test_db.commit()
        
        total = crud.count_media(test_db)
        assert total == 5
        
        approved_count = crud.count_media(test_db, approved_only=True)
        assert approved_count == 3
