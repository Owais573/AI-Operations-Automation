"""
Supabase Storage Service -- Upload and manage PDF reports.

Provides helpers to upload generated PDF files to Supabase Storage
and generate public/signed URLs for download.
"""

import os
from backend.database.db import get_db
from backend.utils.logger import get_logger

logger = get_logger("storage")

BUCKET_NAME = "reports"


async def upload_pdf(file_path: str, run_id: str) -> dict:
    """
    Upload a PDF report to Supabase Storage.

    Args:
        file_path: Local path to the generated PDF file.
        run_id: Workflow run ID (used to organize files).

    Returns:
        dict with 'storage_path' and 'public_url'.
    """
    if not os.path.exists(file_path):
        logger.warning(f"PDF file not found: {file_path}")
        return {"status": "skipped", "detail": "File not found"}

    db = get_db()
    filename = os.path.basename(file_path)
    storage_path = f"{run_id}/{filename}"

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Upload to Supabase Storage
        db.client.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"},
        )

        # Generate public URL
        public_url = db.client.storage.from_(BUCKET_NAME).get_public_url(storage_path)

        logger.info(f"PDF uploaded: {storage_path}")
        return {
            "status": "uploaded",
            "storage_path": storage_path,
            "public_url": public_url,
        }

    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        return {"status": "failed", "detail": str(e)}


async def get_download_url(storage_path: str, expires_in: int = 3600) -> str | None:
    """
    Generate a signed download URL for a stored PDF.

    Args:
        storage_path: Path in the storage bucket.
        expires_in: URL expiry time in seconds (default 1 hour).

    Returns:
        Signed URL string, or None on failure.
    """
    try:
        db = get_db()
        result = db.client.storage.from_(BUCKET_NAME).create_signed_url(
            storage_path, expires_in
        )
        return result.get("signedURL")
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        return None


async def delete_file(storage_path: str) -> bool:
    """
    Remove a file from Supabase Storage.

    Args:
        storage_path: Path in the reports bucket.

    Returns:
        True if successful or file already gone, False otherwise.
    """
    try:
        db = get_db()
        db.client.storage.from_(BUCKET_NAME).remove([storage_path])
        logger.info(f"Deleted file from storage: {storage_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete file from storage {storage_path}: {e}")
        return False
