from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from pushikoo.model.cron import Cron, CronCreate, CronListFilter, CronUpdate
from pushikoo.model.pagination import Page
from pushikoo.service.refresh import CronService


router = APIRouter(prefix="/crons", tags=["crons"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_cron(payload: CronCreate) -> Cron:
    return CronService.create(payload)


@router.get("")
def list_crons(
    flow_id: UUID | None = None,
    cron: str | None = None,
    enabled: bool | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Page[Cron]:
    filter_obj = CronListFilter(
        flow_id=flow_id,
        cron=cron,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return CronService.list(filter_obj)


@router.patch("/{cron_id}")
def update_cron(cron_id: UUID, payload: CronUpdate) -> Cron:
    try:
        return CronService.update(cron_id, payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cron not found"
        )


@router.delete(
    "/{cron_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cron(cron_id: UUID) -> Response:
    try:
        CronService.delete(cron_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cron not found"
        )
