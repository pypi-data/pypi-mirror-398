from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from pushikoo.model.adapter import AdapterMeta
from pushikoo.service.adapter import AdapterService

router = APIRouter(prefix="/adapters", tags=["adapters"])


@router.get("")
def list_adapters() -> list[AdapterMeta]:
    return [meta for _, meta in AdapterService.list_all_adapter_with_type()]


@router.get("/{adapter_name}/config")
def get_adapter_config(adapter_name: str) -> dict:
    try:
        return AdapterService.get_config(adapter_name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter not found"
        )


@router.put("/{adapter_name}/config")
def set_adapter_config(adapter_name: str, config: dict[str, Any]) -> dict:
    try:
        return AdapterService.set_config(adapter_name, config)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(e.errors()),
        )


@router.get("/{adapter_name}/config/schema")
def get_adapter_config_schema(adapter_name: str) -> dict:
    try:
        return AdapterService.get_config_jsonschema(adapter_name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter not found"
        )


@router.get("/{adapter_name}/instance-config/schema")
def get_adapter_instance_config_schema(adapter_name: str) -> dict:
    try:
        return AdapterService.get_instance_config_jsonschema(adapter_name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adapter not found"
        )
