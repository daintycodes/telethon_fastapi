from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    active = Column(Boolean, default=True)

class MediaFile(Base):
    __tablename__ = "media_files"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, unique=True, index=True)
    channel_username = Column(String)
    file_name = Column(String)
    file_type = Column(String)  # audio/pdf
    s3_key = Column(String)
    downloaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved = Column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
