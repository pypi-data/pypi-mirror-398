from uuid import UUID

from pydantic import BaseModel


class CronCreate(BaseModel):
    flow_id: UUID
    cron: str
    enabled: bool = True


class CronUpdate(BaseModel):
    cron: str | None = None
    enabled: bool | None = None


class CronListFilter(BaseModel):
    flow_id: UUID | None = None
    cron: str | None = None
    enabled: bool | None = None
    limit: int | None = None
    offset: int | None = None


class Cron(BaseModel):
    id: UUID
    flow_id: UUID
    cron: str
    enabled: bool
