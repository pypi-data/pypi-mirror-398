"""
File API - Public access to stored files.
"""

import datetime
import mimetypes
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from pushikoo.service.image import ImageService
from pushikoo.util.setting import FILE_DIR

router = APIRouter(prefix="/file", tags=["file"])


@router.get("/{access_id}")
def get_file(access_id: UUID) -> FileResponse:
    """
    Get a file by its access ID.

    This endpoint is public and does not require authentication.
    Returns the file if it exists and has not expired.
    """
    # Get file record from database
    file_record = ImageService.get_file_by_id(access_id)

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Check expiration
    now = datetime.datetime.now(datetime.timezone.utc)
    if file_record.expire_at < now:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File has expired",
        )

    # Get file path
    file_path = FILE_DIR / file_record.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    # Determine MIME type from filename
    media_type, _ = mimetypes.guess_type(file_record.filename)
    if not media_type:
        # Default to octet-stream if unknown
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={"Content-Disposition": "inline"},
    )
