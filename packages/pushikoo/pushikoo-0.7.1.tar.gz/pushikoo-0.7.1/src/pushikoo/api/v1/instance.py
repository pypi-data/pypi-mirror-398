from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from pushikoo.model.adapter import (
    AdapterInstance,
    AdapterInstanceCreate,
    AdapterInstanceListFilter,
)
from pushikoo.model.pagination import Page
from pushikoo.service.adapter import AdapterInstanceService

router = APIRouter(prefix="/instances", tags=["instances"])


@router.get("")
def list_instances(
    adapter_name: str | None = None,
    identifier: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Page[AdapterInstance]:
    """List all adapter instances with optional filtering."""
    filter_obj = AdapterInstanceListFilter(
        adapter_name=adapter_name,
        identifier=identifier,
        limit=limit,
        offset=offset,
    )
    return AdapterInstanceService.list(filter_obj)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_instance(instance_create: AdapterInstanceCreate) -> AdapterInstance:
    """Create a new adapter instance."""
    try:
        return AdapterInstanceService.create(instance_create)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter not found"
        )


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instance(instance_id: UUID) -> Response:
    """Delete an adapter instance by ID."""
    try:
        instance = AdapterInstanceService.get(instance_id)
        AdapterInstanceService.delete(instance.adapter_name, instance.identifier)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter instance not found"
        )


@router.get("/{instance_id}/config")
def get_instance_config(instance_id: UUID) -> dict:
    """Get configuration for an adapter instance by ID."""
    try:
        instance = AdapterInstanceService.get(instance_id)
        config = AdapterInstanceService.get_config(
            instance.adapter_name, instance.identifier
        )
        return config.model_dump()
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter instance not found"
        )


@router.put("/{instance_id}/config")
def set_instance_config(instance_id: UUID, config: dict[str, Any]) -> dict:
    """Set configuration for an adapter instance by ID."""
    try:
        instance = AdapterInstanceService.get(instance_id)
        return AdapterInstanceService.set_config(
            instance.adapter_name, instance.identifier, config
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter instance not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(e.errors()),
        )
