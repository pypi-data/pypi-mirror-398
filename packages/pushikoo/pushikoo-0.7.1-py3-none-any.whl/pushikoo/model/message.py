from enum import StrEnum
from uuid import UUID

from pushikoo_interface import Struct
from pydantic import BaseModel


class MessageOrder(StrEnum):
    TS_DESC = "ts_desc"
    TS_ASC = "ts_asc"
    IDENTIFIER_ASC = "identifier_asc"
    IDENTIFIER_DESC = "identifier_desc"
    GETTER_NAME_ASC = "getter_name_asc"
    GETTER_NAME_DESC = "getter_name_desc"


class MessageCreate(BaseModel):
    message_identifier: str
    getter_name: str
    ts: float
    content: Struct


class MessageUpdate(BaseModel):
    message_identifier: str | None = None
    getter_name: str | None = None
    ts: float | None = None
    content: Struct | None = None


class MessageListFilter(BaseModel):
    message_identifier: str | None = None
    getter_name: str | None = None
    ts: float | None = None
    content: Struct | None = None
    ts_from: float | None = None
    ts_to: float | None = None
    keywords: str | None = None
    limit: int | None = None
    offset: int | None = None
    order: MessageOrder = MessageOrder.TS_DESC


class Message(BaseModel):
    id: UUID
    message_identifier: str
    getter_name: str
    ts: float
    content: Struct
