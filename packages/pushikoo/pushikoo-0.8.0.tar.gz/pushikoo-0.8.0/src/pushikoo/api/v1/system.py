from typing import Any

from fastapi import APIRouter

from pushikoo.model.config import SystemConfig
from pushikoo.service.config import ConfigService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/config")
def get_system_config() -> SystemConfig:
    return ConfigService(id_="system", model_type=SystemConfig).get()


@router.put("/config")
def set_system_config(config: dict[str, Any]) -> SystemConfig:
    cfg = SystemConfig.model_validate(config)
    service = ConfigService(id_="system", model_type=SystemConfig)
    service.set(cfg)
    return service.get()


@router.get("/config/schema")
def get_system_config_schema() -> dict:
    return SystemConfig.model_json_schema()
