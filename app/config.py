import os

# Telegram API credentials
API_ID = int(os.getenv("TG_API_ID", "YOUR_API_ID"))
API_HASH = os.getenv("TG_API_HASH", "YOUR_API_HASH")
SESSION_NAME = os.getenv("TG_SESSION", "telethon_session")

# S3/MinIO config
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET_AUDIO = os.getenv("S3_BUCKET_AUDIO", "audio")
S3_BUCKET_PDF = os.getenv("S3_BUCKET_PDF", "pdf")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./telethon.db")
