from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from pushikoo.model.adapter import AdapterInstance
from pushikoo.model.pagination import Page
from pushikoo.model.warning import WarningRecipientCreate
from pushikoo.service.warning import WarningService


router = APIRouter(prefix="/warnings", tags=["warnings"])


@router.post("/recipients", status_code=status.HTTP_201_CREATED)
def add_recipient(payload: WarningRecipientCreate) -> AdapterInstance:
    try:
        return WarningService.add_recipient(payload.adapter_instance_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter instance not found"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Recipient already exists"
        )


@router.get("/recipients")
def list_recipients(
    limit: int | None = None,
    offset: int | None = None,
) -> Page[AdapterInstance]:
    return WarningService.list_recipients(limit=limit, offset=offset)


@router.delete(
    "/recipients/{adapter_instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_recipient(adapter_instance_id: UUID) -> Response:
    try:
        WarningService.remove_recipient(adapter_instance_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (KeyError, LookupError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found"
        )
