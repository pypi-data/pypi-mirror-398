from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from pushikoo.model.pip import PipCommandResult
from pushikoo.service.pip import PIPService
from pushikoo.util.setting import CACHE_DIR as BASE_CACHE_DIR

CACHE_DIR = BASE_CACHE_DIR / "api" / "pip"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/pip", tags=["pip"])


@router.post(
    "/pkgs/whl", status_code=status.HTTP_200_OK, response_model=PipCommandResult
)
def install_package_by_whl(
    file: UploadFile = File(...),
    force: bool = False,
    upgrade: bool = False,
    index_url: str | None = None,
    extra_index_urls: list[str] | None = Query(default=None),
) -> PipCommandResult:
    filename = Path(file.filename or "").name
    if not filename or not filename.lower().endswith(".whl"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a .whl"
        )

    dest_path = CACHE_DIR / uuid4().hex / filename
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with dest_path.open("wb") as f:
            for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
                f.write(chunk)
        result = PIPService.install(
            dest_path,
            force=force,
            upgrade=upgrade,
            index_url=index_url,
            extra_index_urls=extra_index_urls,
        )
        if result.get("ok"):
            return PipCommandResult(target=result["target"], output=result["output"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["output"]
        )
    finally:
        try:
            file.file.close()
        except Exception:
            pass


@router.post(
    "/pkgs/{spec}", status_code=status.HTTP_200_OK, response_model=PipCommandResult
)
def install_package(
    spec: str,
    force: bool = False,
    upgrade: bool = False,
    index_url: str | None = None,
    extra_index_urls: list[str] | None = Query(default=None),
) -> PipCommandResult:
    target = spec if not spec.strip().startswith(".") else str(Path(spec).resolve())
    result = PIPService.install(
        target,
        force=force,
        upgrade=upgrade,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
    )
    if result.get("ok"):
        return PipCommandResult(target=result["target"], output=result["output"])
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=result["output"]
    )


@router.delete(
    "/pkgs/{package_name}",
    status_code=status.HTTP_200_OK,
    response_model=PipCommandResult,
)
def uninstall_package(
    package_name: str,
) -> PipCommandResult:
    result = PIPService.uninstall(package_name)
    if result.get("ok"):
        return PipCommandResult(target=result["target"], output=result["output"])
    # "not installed" or other pip errors are exposed directly
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=result["output"]
    )


@router.get("/indexes")
def list_indexes(
    limit: int | None = None,
    offset: int | None = None,
) -> list[str]:
    return PIPService.list_indexes(limit=limit, offset=offset)


@router.get("/indexes/{url:path}")
def get_index(url: str) -> str:
    urls = PIPService.list_indexes()
    if url in urls:
        return url
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.post("/indexes/{url:path}", status_code=status.HTTP_201_CREATED)
def add_index(url: str) -> str:
    try:
        return PIPService.add_index(url)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict")


@router.delete("/indexes/{url:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_index(url: str) -> Response:
    PIPService.delete_index(url)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
