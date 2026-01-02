from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from pushikoo.model.flow import (
    Flow,
    FlowCreate,
    FlowExecuteRequest,
    FlowInstance,
    FlowInstanceDetail,
    FlowInstanceListFilter,
    FlowInstanceOrder,
    FlowInstanceStatus,
    FlowListFilter,
    FlowUpdate,
)
from pushikoo.model.pagination import Page
from pushikoo.service.refresh import (
    FlowInstanceRunner,
    FlowInstanceService,
    FlowNodeExecutionService,
    FlowService,
)


router = APIRouter(prefix="/flows", tags=["flows"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_flow(payload: FlowCreate) -> Flow:
    return FlowService.create(payload)


@router.get("")
def list_flows(
    getter_instance_id: UUID | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Page[Flow]:
    filter_obj = FlowListFilter(
        getter_instance_id=getter_instance_id,
        limit=limit,
        offset=offset,
    )
    return FlowService.list_(filter_obj)


@router.get("/instances")
def list_flow_instances(
    flow_id: UUID | None = None,
    status: FlowInstanceStatus | None = None,
    limit: int | None = None,
    offset: int | None = None,
    order: FlowInstanceOrder = FlowInstanceOrder.CREATED_AT_DESC,
) -> Page[FlowInstance]:
    filter_obj = FlowInstanceListFilter(
        flow_id=flow_id,
        status=status,
        limit=limit,
        offset=offset,
        order=order,
    )
    return FlowInstanceService.list_(filter_obj)


@router.get("/instances/{instance_id}")
def get_flow_instance(instance_id: UUID) -> FlowInstance:
    try:
        return FlowInstanceService.get(instance_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow instance not found",
        )


@router.get("/instances/{instance_id}/detail")
def get_flow_instance_detail(instance_id: UUID) -> FlowInstanceDetail:
    """Get detailed execution information for a flow instance."""
    try:
        instance = FlowInstanceService.get(instance_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow instance not found",
        )

    node_executions = FlowNodeExecutionService.list_by_instance(instance_id)

    return FlowInstanceDetail(
        id=instance.id,
        flow_id=instance.flow_id,
        status=instance.status,
        created_at=instance.created_at,
        node_executions=node_executions,
    )


@router.get("/{flow_id}")
def get_flow(flow_id: UUID) -> Flow:
    try:
        return FlowService.get(flow_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found"
        )


@router.put("/{flow_id}")
def update_flow(flow_id: UUID, payload: FlowUpdate) -> Flow:
    try:
        return FlowService.update(flow_id, payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found"
        )


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flow(flow_id: UUID) -> Response:
    try:
        FlowService.delete(flow_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found"
        )


@router.post("/{flow_id}/execute", status_code=status.HTTP_204_NO_CONTENT)
def execute_flow(flow_id: UUID, payload: FlowExecuteRequest | None = None) -> Response:
    """Manually trigger a flow execution with optional node exclusions."""
    try:
        FlowService.get(flow_id)  # Validate flow exists
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found"
        )

    include_nodes = payload.include_nodes if payload else None
    runner = FlowInstanceRunner(flow_id, include_nodes=include_nodes)
    runner.do()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
