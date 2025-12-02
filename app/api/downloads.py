import aiofiles
import os
from minio import Minio
from fastapi import HTTPException
from typing import Optional
from uuid import uuid4

from .config import (
    S3_ENDPOINT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET_AUDIO,
    S3_BUCKET_PDF
)

# Initialize MinIO client
s3 = Minio(
    S3_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=S3_ENDPOINT.startswith("https://")
)

# Ensure buckets exist
for bucket in [S3_BUCKET_AUDIO, S3_BUCKET_PDF]:
    if not s3.bucket_exists(bucket):
        s3.make_bucket(bucket)


async def save_temp_file(byte_data: bytes, filename: str) -> str:
    """Save file temporarily before uploading to S3."""
    path = f"downloads/{filename}"
    os.makedirs("downloads", exist_ok=True)

    async with aiofiles.open(path, "wb") as f:
        await f.write(byte_data)

    return path


async def upload_to_s3(local_path: str, bucket: str, object_name: Optional[str] = None) -> str:
    """Upload file to MinIO and return the object URL."""
    if object_name is None:
        object_name = f"{uuid4()}-{os.path.basename(local_path)}"

    try:
        size = os.path.getsize(local_path)
        with open(local_path, "rb") as f:
            s3.put_object(bucket, object_name, data=f, length=size)

        return f"{bucket}/{object_name}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def store_media(byte_data: bytes, file_name: str, media_type: str) -> str:
    """Store either PDF or Audio into appropriate bucket."""
    # Determine bucket
    if media_type == "audio":
        bucket = S3_BUCKET_AUDIO
    elif media_type == "pdf":
        bucket = S3_BUCKET_PDF
    else:
        raise ValueError("Invalid media type. Must be 'audio' or 'pdf'.")

    # Save temporarily
    local_path = await save_temp_file(byte_data, file_name)

    # Upload to S3
    s3_key = await upload_to_s3(local_path, bucket)

    # Remove local temp file
    try:
        os.remove(local_path)
    except:
        pass

    return s3_key
