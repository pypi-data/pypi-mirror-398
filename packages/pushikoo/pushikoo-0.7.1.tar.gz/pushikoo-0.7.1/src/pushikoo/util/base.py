import hashlib
import logging
import mimetypes
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

import diskcache
import requests
from PIL import Image

from pushikoo.util.setting import CACHE_DIR as BASE_CACHE_DIR

DISKCACHE_CACHE_DIR = BASE_CACHE_DIR / "diskcache"
DISKCACHE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

cache = diskcache.Cache(directory=DISKCACHE_CACHE_DIR)


def download_with_cache(
    url: str,
    path: Path,
    filename: str = "",
    expire: int = 3 * 24 * 3600,
    force: bool = False,
) -> tuple[Path, bool]:
    """
    Download a file from a URL with local caching.

    Args:
        url (str): The download URL.
        path (Path): Target directory to save the file.
        filename (str, optional): Output filename. If empty, inferred from URL or Content-Type.
        expire (int, optional): Cache expiration time in seconds. Defaults to 3 days.
        force (bool, optional): If True, skip cache and force download.

    Returns:
        tuple[Path, bool]: (saved_file_path, cache_hit)
    """
    key = f"download::{url}"
    cache_dir = Path.home() / ".cache" / "download_with_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / (key.replace("::", "_").replace("/", "_"))

    if not force and cache_file.exists():
        cached_path = Path(cache_file.read_text().strip())
        if cached_path.exists():
            logging.info(f"Cache hit: {cached_path}")
            return cached_path, True
        cache_file.unlink(missing_ok=True)

    logging.info(f"Downloading: {url}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    final_filename = filename.strip()
    if not final_filename:
        parsed = urlparse(url)
        guessed_name = Path(parsed.path).name
        if guessed_name:
            final_filename = guessed_name
        else:
            content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
            ext = mimetypes.guess_extension(content_type)
            if ext:
                final_filename = f"download{ext}"
            else:
                raise ValueError(
                    f"Cannot determine filename from URL or Content-Type ({content_type})"
                )

    save_path = path / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with save_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    cache_file.write_text(str(save_path))
    logging.info(f"Cached: {save_path} (expires in {expire}s)")

    return save_path, False


def generate_function_call_str(function, *args, **kwargs):
    args_str = ", ".join(repr(arg) for arg in args)
    kwargs_str = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
    all_args_str = ", ".join(filter(None, [args_str, kwargs_str]))
    return f"{function}({all_args_str})"


def is_valid_url(url):
    if url is None:
        return False
    pattern = re.compile(
        r"^(https?|ftp)://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(pattern, url) is not None


def byte_to_MB(byte):
    return byte / (1024**2)


def is_local_or_url(path_str: str) -> str:
    path_str = path_str.strip()
    parsed = urlparse(path_str)
    if parsed.scheme in ["http", "https"] and parsed.netloc:
        return "url"
    path = Path(path_str)
    if path.exists() or path_str.startswith(("/", "./", "../", "~")):
        return "local"
    if not re.match(r"^https?://", path_str):
        return "local"
    return "unknown"


def get_image_mime_suffix(file_path: str) -> str:
    FORMAT_TO_MIME_SUFFIX = {
        "JPEG": "jpeg",
        "PNG": "png",
        "GIF": "gif",
        "BMP": "bmp",
        "TIFF": "tiff",
        "WEBP": "webp",
    }
    try:
        with Image.open(file_path) as img:
            fmt = img.format
            suffix = FORMAT_TO_MIME_SUFFIX.get(fmt.upper())
            if suffix:
                return suffix
            else:
                raise ValueError(f"Unsupported image format: {fmt}")
    except Exception as e:
        raise ValueError(f"Cannot open image file: {e}")


def file_uuid(path: Path) -> uuid.UUID:
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    digest = sha256.hexdigest()
    return uuid.uuid5(uuid.NAMESPACE_URL, digest)
