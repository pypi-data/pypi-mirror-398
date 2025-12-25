from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class FlowCreate(BaseModel):
    name: str = ""
    nodes: list[UUID]


class FlowUpdate(BaseModel):
    name: str | None = None
    nodes: list[UUID] | None = None


class FlowListFilter(BaseModel):
    getter_instance_id: UUID | None = None  # filter by first node (= getter)
    limit: int | None = None
    offset: int | None = None


class Flow(BaseModel):
    id: UUID
    name: str
    nodes: list[UUID]


class FlowInstanceStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FlowInstanceOrder(StrEnum):
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"


class FlowInstanceListFilter(BaseModel):
    flow_id: UUID | None = None
    status: FlowInstanceStatus | None = None
    limit: int | None = None
    offset: int | None = None
    order: FlowInstanceOrder = FlowInstanceOrder.CREATED_AT_DESC


class FlowInstance(BaseModel):
    id: UUID
    flow_id: UUID
    status: FlowInstanceStatus
    created_at: datetime


class FlowExecuteRequest(BaseModel):
    """Request body for executing a flow with optional node inclusions."""

    include_nodes: list[UUID] | None = None  # List of node IDs to run (None = run all)
