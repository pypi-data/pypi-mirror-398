from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from pushikoo.model.message import (
    Message,
    MessageCreate,
    MessageListFilter,
    MessageOrder,
    MessageUpdate,
)
from pushikoo.model.pagination import Page
from pushikoo.service.message import MessageService


router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_message(payload: MessageCreate) -> Message:
    return MessageService.create(payload)


@router.get("")
def list_messages(
    message_identifier: str | None = None,
    getter_name: str | None = None,
    ts: float | None = None,
    ts_from: float | None = None,
    ts_to: float | None = None,
    keywords: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    order: MessageOrder = MessageOrder.TS_DESC,
) -> Page[Message]:
    filter_obj = MessageListFilter(
        message_identifier=message_identifier,
        getter_name=getter_name,
        ts=ts,
        ts_from=ts_from,
        ts_to=ts_to,
        keywords=keywords,
        limit=limit,
        offset=offset,
        order=order,
    )
    return MessageService.list(filter_obj)


@router.get("/{message_id}")
def get_message(message_id: UUID) -> Message:
    try:
        return MessageService.get(message_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: UUID) -> Response:
    try:
        MessageService.delete(message_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )


@router.patch("/{message_id}")
def update_message(message_id: UUID, payload: MessageUpdate) -> Message:
    return MessageService.update(message_id, payload)
