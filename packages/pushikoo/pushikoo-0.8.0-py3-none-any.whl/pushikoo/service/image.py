"""
ImageService - Handle image URIs, store locally, and provide access links.
"""

import datetime
import hashlib
import shutil
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from loguru import logger
from PIL import Image
from sqlmodel import select

from pushikoo.db import File as FileDB
from pushikoo.db import get_session
from pushikoo.util.setting import (
    FILE_DIR,
    IMAGE_LINK_DEFAULT_EXPIRE_SECOND,
    settings,
)

# Format to MIME suffix mapping
FORMAT_TO_SUFFIX = {
    "JPEG": "jpeg",
    "PNG": "png",
    "GIF": "gif",
    "BMP": "bmp",
    "TIFF": "tiff",
    "WEBP": "webp",
}


class ImageService:
    @staticmethod
    def create(uri: str) -> str:
        """
        Process an image URI and return an access link.

        Args:
            uri: Image URI (file:/// or http(s)://)

        Returns:
            Access URL: BACKEND_BASE_HOST + /file/{uuid}
        """
        try:
            # Parse URI and get image data
            image_path = ImageService._resolve_uri_to_file(uri)

            # Calculate SHA256 hash
            file_hash = ImageService._calculate_hash(image_path)

            # Detect image format using PIL
            suffix = ImageService._detect_image_format(image_path)

            # Construct filename
            filename = f"{file_hash}.{suffix}"
            target_path = FILE_DIR / filename

            # Copy/move to FILE_DIR if not already there
            if not target_path.exists():
                shutil.copy2(image_path, target_path)
                logger.debug(f"Saved image to {target_path}")

            # Generate UUID and calculate expire_at
            file_id = uuid.uuid4()
            expire_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=IMAGE_LINK_DEFAULT_EXPIRE_SECOND)

            # Store in database
            with get_session() as session:
                file_record = FileDB(
                    id=file_id,
                    filename=filename,
                    expire_at=expire_at,
                )
                session.add(file_record)
                session.commit()
                logger.debug(f"Created file record: {file_id} -> {filename}")

            # Return access URL
            access_url = f"{settings.BACKEND_BASE_HOST}/file/{file_id}"
            return access_url

        except Exception as e:
            logger.warning(f"ImageService.create failed for {uri}: {e}")
            # Return original URI on failure
            return uri

    @staticmethod
    def _resolve_uri_to_file(uri: str) -> Path:
        """
        Resolve URI to a local file path.
        Downloads remote files to a temp location if needed.
        """
        parsed = urlparse(uri)

        if parsed.scheme == "file":
            # file:/// URI - extract local path
            # On Windows: file:///C:/path -> C:/path
            # On Unix: file:///path -> /path
            local_path = parsed.path
            if (
                local_path.startswith("/")
                and len(local_path) > 2
                and local_path[2] == ":"
            ):
                # Windows path like /C:/path
                local_path = local_path[1:]
            return Path(local_path)

        elif parsed.scheme in ("http", "https"):
            # Download to temp file
            response = requests.get(uri, stream=True, timeout=30)
            response.raise_for_status()

            # Create temp file
            suffix = Path(parsed.path).suffix or ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                return Path(tmp.name)

        elif not parsed.scheme:
            # Plain local path
            return Path(uri)

        else:
            raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")

    @staticmethod
    def _calculate_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _detect_image_format(file_path: Path) -> str:
        """Detect image format using PIL and return file suffix."""
        with Image.open(file_path) as img:
            fmt = img.format
            if fmt and fmt.upper() in FORMAT_TO_SUFFIX:
                return FORMAT_TO_SUFFIX[fmt.upper()]
            raise ValueError(f"Unsupported image format: {fmt}")

    @staticmethod
    def get_file_by_id(file_id: uuid.UUID) -> FileDB | None:
        """Get file record by ID."""
        with get_session() as session:
            return session.exec(select(FileDB).where(FileDB.id == file_id)).first()
