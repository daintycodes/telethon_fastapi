"""S3/MinIO storage utilities with async-safe operations."""

import asyncio
import os
from functools import lru_cache
from uuid import uuid4
from typing import Optional

from minio import Minio
from datetime import timedelta
from fastapi import HTTPException

from .config import (
    S3_ENDPOINT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET_AUDIO,
    S3_BUCKET_PDF,
)


@lru_cache(maxsize=1)
def get_s3_client() -> Minio:
    """Get or create MinIO client (cached as singleton).
    
    Returns:
        Minio: Configured MinIO client.
    """
    endpoint = S3_ENDPOINT.replace("http://", "").replace("https://", "")
    secure = S3_ENDPOINT.startswith("https://")
    
    s3 = Minio(
        endpoint,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        secure=secure
    )
    return s3


def ensure_buckets_exist() -> None:
    """Create S3 buckets if they don't exist.
    
    Raises:
        Exception: If bucket creation fails.
    """
    s3 = get_s3_client()
    for bucket in [S3_BUCKET_AUDIO, S3_BUCKET_PDF]:
        try:
            if not s3.bucket_exists(bucket):
                s3.make_bucket(bucket)
        except Exception as e:
            raise RuntimeError(f"Failed to ensure bucket {bucket} exists: {e}")


async def save_temp_file(byte_data: bytes, filename: str) -> str:
    """Save file temporarily before uploading to S3 (async).
    
    Args:
        byte_data: File content as bytes.
        filename: Target filename.
        
    Returns:
        str: Local path to saved file.
    """
    path = f"downloads/{filename}"
    os.makedirs("downloads", exist_ok=True)
    
    # Write file asynchronously using thread executor
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write_file, path, byte_data)
    return path


def _write_file(path: str, data: bytes) -> None:
    """Synchronous file write helper (runs in thread executor).
    
    Args:
        path: File path.
        data: Bytes to write.
    """
    with open(path, "wb") as f:
        f.write(data)


async def upload_to_s3(
    local_path: str,
    bucket: str,
    object_name: Optional[str] = None
) -> str:
    """Upload file to MinIO (async-safe via thread executor).
    
    Args:
        local_path: Path to local file.
        bucket: S3 bucket name.
        object_name: Optional S3 object name; auto-generated if not provided.
        
    Returns:
        str: S3 key in format "bucket/object".
        
    Raises:
        HTTPException: If upload fails.
    """
    if object_name is None:
        object_name = f"{uuid4()}-{os.path.basename(local_path)}"
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            _upload_file_sync,
            local_path,
            bucket,
            object_name
        )
        return f"{bucket}/{object_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _upload_file_sync(local_path: str, bucket: str, object_name: str) -> None:
    """Synchronous S3 upload helper (runs in thread executor).
    
    Args:
        local_path: Path to local file.
        bucket: S3 bucket name.
        object_name: S3 object name.
    """
    s3 = get_s3_client()
    size = os.path.getsize(local_path)
    with open(local_path, "rb") as f:
        s3.put_object(bucket, object_name, data=f, length=size)


async def store_media(
    byte_data: bytes,
    file_name: str,
    media_type: str
) -> str:
    """Store PDF or audio file into appropriate S3 bucket.
    
    Args:
        byte_data: File content as bytes.
        file_name: Filename.
        media_type: Either "audio" or "pdf".
        
    Returns:
        str: S3 key in format "bucket/object".
        
    Raises:
        ValueError: If media_type is invalid.
        HTTPException: If upload fails.
    """
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
    
    # Remove local temp file asynchronously
    await asyncio.to_thread(_cleanup_file, local_path)
    
    return s3_key


def _cleanup_file(path: str) -> None:
    """Synchronous file cleanup helper (runs in thread executor).
    
    Args:
        path: File path to remove.
    """
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def get_presigned_url(bucket: str, object_name: str, expiration: int = 3600) -> str:
    """Get presigned download URL for S3 object.
    
    Args:
        bucket: S3 bucket name.
        object_name: S3 object name.
        expiration: URL expiration time in seconds (default 1 hour).
        
    Returns:
        str: Presigned URL.
    """
    s3 = get_s3_client()
    # MinIO client expects a timedelta for expires
    try:
        expires = timedelta(seconds=int(expiration))
    except Exception:
        expires = timedelta(seconds=3600)

    # Use the MinIO method to generate a presigned GET URL
    return s3.presigned_get_object(bucket, object_name, expires=expires)
