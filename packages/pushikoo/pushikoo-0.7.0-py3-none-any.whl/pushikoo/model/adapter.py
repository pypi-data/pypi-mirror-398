from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel
from pushikoo_interface import AdapterMeta as InterfaceAdapterMeta


class AdapterType(StrEnum):
    GETTER = "getter"
    PUSHER = "pusher"
    PROCESSER = "processer"


class AdapterMeta(InterfaceAdapterMeta):
    type: AdapterType


class AdapterInstanceBase(BaseModel):
    adapter_name: str
    identifier: str


class AdapterInstanceCreate(AdapterInstanceBase):
    pass


class AdapterInstanceUpdate(BaseModel):
    adapter_name: str | None = None
    identifier: str | None = None


class AdapterInstanceListFilter(BaseModel):
    adapter_name: str | None = None
    identifier: str | None = None
    limit: int | None = None
    offset: int | None = None


class AdapterInstance(AdapterInstanceBase):
    id: UUID
