from pathlib import Path
from importlib.resources import files

from fastapi import APIRouter
from fastapi.responses import FileResponse

import pushikoo
from pushikoo.util.setting import settings

router = APIRouter(tags=["spa"])

internal_static = files(pushikoo) / "frontend-static"
external_static = Path("static")


def serve_file(path: Path):
    if path.name == "index.html":
        return FileResponse(path, headers={"Cache-Control": "no-store"})
    return FileResponse(
        path, headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )


@router.get("/")
def serve_index():
    if settings.ENVIRONMENT == "local":
        external_index = external_static / "index.html"
        if external_index.is_file():
            return serve_file(external_index)
    return serve_file(internal_static / "index.html")


@router.get("/{full_path:path}")
def serve_spa(full_path: str):
    if settings.ENVIRONMENT == "local":
        external_path = external_static / full_path
        if external_path.is_file():
            return serve_file(external_path)

    internal_path = internal_static / full_path
    if internal_path.is_file():
        return serve_file(internal_path)

    if settings.ENVIRONMENT == "local":
        external_index = external_static / "index.html"
        if external_index.is_file():
            return serve_file(external_index)

    return serve_file(internal_static / "index.html")
