import os

# Telegram API credentials
API_ID_STR = os.getenv("TG_API_ID")
if not API_ID_STR or not API_ID_STR.isdigit():
    raise ValueError(
        "Missing or invalid TG_API_ID environment variable. "
        "Must be a valid integer. Set via TG_API_ID environment variable."
    )
API_ID = int(API_ID_STR)

API_HASH = os.getenv("TG_API_HASH")
if not API_HASH:
    raise ValueError(
        "Missing TG_API_HASH environment variable. "
        "Set via TG_API_HASH environment variable."
    )

# Session file location - use /data to avoid conflict with /app volume mount
SESSION_NAME = os.getenv("TG_SESSION", "/data/telethon_session")

# Optional admin API key for protecting admin endpoints
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# Optional Sentry DSN for error monitoring
SENTRY_DSN = os.getenv("SENTRY_DSN")

# S3/MinIO config
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET_AUDIO = os.getenv("S3_BUCKET_AUDIO", "audio")
S3_BUCKET_PDF = os.getenv("S3_BUCKET_PDF", "pdf")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./telethon.db")
