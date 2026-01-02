from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from loguru import logger
from pushikoo_interface import (
    Adapter,
    AdapterFrameworkContext as AdapterFrameworkContextInterface,
)
from pushikoo_interface import Adapter as InterfaceAdapter
from pushikoo_interface import (
    AdapterMeta as InterfaceAdapterMeta,
    Getter,
    Processer,
    Pusher,
    get_adapter_config_types,
)
from pydantic import ValidationError
from sqlmodel import select

from pushikoo.db import AdapterInstance as AdapterInstanceDB
from pushikoo.db import get_session
from pushikoo.model.adapter import (
    AdapterInstance,
    AdapterInstanceCreate,
    AdapterInstanceListFilter,
    AdapterMeta,
    AdapterType,
)
from pushikoo.model.config import SystemConfig
from pushikoo.service.config import ConfigService
from pushikoo.util.setting import DATA_DIR
from sqlmodel import func
from pushikoo.model.pagination import Page, apply_page_limit

ADAPTER_ENTRY_GROUP = "pushikoo.adapter"


class AdapterFrameworkContext(AdapterFrameworkContextInterface):
    storage_base_path: Path = DATA_DIR / "adapters" / "storage"

    def get_proxies(self) -> dict[str, str]:
        return ConfigService("system", SystemConfig).get().network.proxies


class AdapterService:
    """Service for managing adapter discovery and instantiation."""

    @staticmethod
    def _discover() -> list[EntryPoint]:
        """Discover all adapter entry points."""
        return list(entry_points().select(group=ADAPTER_ENTRY_GROUP))

    @staticmethod
    def list_all_adapter() -> list[tuple[type, InterfaceAdapterMeta]]:
        """List all available adapter classes with their metadata (without type)."""
        adapters: list[tuple[type, InterfaceAdapterMeta]] = []
        for ep in AdapterService._discover():
            cls = ep.load()
            meta = getattr(cls, "meta", None)
            if not isinstance(meta, InterfaceAdapterMeta):
                raise TypeError(f"Adapter {ep.name} has invalid or missing meta")
            adapters.append((cls, meta))
        return adapters

    @staticmethod
    def list_all_adapter_with_type() -> list[tuple[type, AdapterMeta]]:
        """List all available adapter classes with metadata including adapter type."""
        result: list[tuple[type, AdapterMeta]] = []

        for cls, meta in AdapterService.list_all_adapter():
            if issubclass(cls, Getter):
                adapter_type = AdapterType.GETTER
            elif issubclass(cls, Pusher):
                adapter_type = AdapterType.PUSHER
            elif issubclass(cls, Processer):
                adapter_type = AdapterType.PROCESSER
            else:
                raise TypeError(
                    f"Adapter {cls.__name__} must be subclass of Getter, Pusher or Processer"
                )

            enriched_meta = AdapterMeta(
                **meta.model_dump(),
                type=adapter_type,
            )
            result.append((cls, enriched_meta))

        return result

    @staticmethod
    def get_clsobj_by_name(adapter_name) -> type[Adapter]:
        """Get adapter class by name."""
        adapter_matched = [
            (adapter_class, adapter_meta)
            for adapter_class, adapter_meta in AdapterService.list_all_adapter()
            if adapter_meta.name == adapter_name
        ]
        if not adapter_matched:
            raise KeyError(f"Adapter class {adapter_name} not found")

        AdapterClass, _adapter_meta = adapter_matched[0]
        return AdapterClass

    @staticmethod
    def create_instance(name: str, identifier: str):
        """Create an adapter instance."""
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, adapter_config_inst_type = get_adapter_config_types(obj)
        ctx = AdapterFrameworkContext()
        ctx.get_config = lambda: ConfigService(name, adapter_config_type).get()
        ctx.get_instance_config = lambda: ConfigService(
            f"{name}.{identifier}", adapter_config_inst_type
        ).get()
        instance = obj.create(identifier=identifier, ctx=ctx)
        logger.debug(f"Created adapter instance: {name}.{identifier}")
        return instance

    @staticmethod
    def get_config(name: str) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, _ = get_adapter_config_types(obj)

        return ConfigService(name, adapter_config_type).get().model_dump()

    @staticmethod
    def set_config(name: str, config_data: dict[str, Any]) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, _ = get_adapter_config_types(obj)
        try:
            config_model = adapter_config_type.model_validate(config_data)
        except ValidationError as e:
            logger.warning(
                f"Failed to validate adapter config for {name} when setting: {e}"
            )
            raise

        ConfigService(name, adapter_config_type).set(config_model)
        return config_model.model_dump()

    @staticmethod
    def get_config_jsonschema(name: str) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, _ = get_adapter_config_types(obj)
        return adapter_config_type.model_json_schema()

    @staticmethod
    def get_instance_config_jsonschema(name: str) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        _, adapter_config_inst_type = get_adapter_config_types(obj)
        return adapter_config_inst_type.model_json_schema()


class AdapterInstanceService:
    instance_objects: dict[UUID, InterfaceAdapter] = {}
    instance_versions: dict[UUID, str] = {}

    @staticmethod
    def get_object(adapter_name: str, identifier: str) -> InterfaceAdapter:
        return next(
            i
            for i in AdapterInstanceService.instance_objects.values()
            if i.adapter_name == adapter_name and i.identifier == identifier
        )

    @staticmethod
    def get_object_by_id(instance_id: UUID) -> InterfaceAdapter:
        with get_session() as session:
            row = session.get(AdapterInstanceDB, instance_id)

        if not row:
            raise KeyError(f"Adapter instance {instance_id} not found")

        adapter_class = AdapterService.get_clsobj_by_name(row.adapter_name)
        current_version = adapter_class.meta.version

        if instance_id in AdapterInstanceService.instance_objects:
            cached_version = AdapterInstanceService.instance_versions.get(instance_id)

            if cached_version != current_version:
                logger.info(
                    f"Adapter version changed for {row.adapter_name}.{row.identifier}: "
                    f"{cached_version} -> {current_version}, re-instantiating"
                )

                del AdapterInstanceService.instance_objects[instance_id]
                del AdapterInstanceService.instance_versions[instance_id]
                new_instance = AdapterService.create_instance(
                    row.adapter_name, row.identifier
                )
                AdapterInstanceService.instance_objects[instance_id] = new_instance
                AdapterInstanceService.instance_versions[instance_id] = current_version

                return new_instance
            else:
                return AdapterInstanceService.instance_objects[instance_id]
        else:
            instance = AdapterService.create_instance(row.adapter_name, row.identifier)
            AdapterInstanceService.instance_objects[instance_id] = instance
            AdapterInstanceService.instance_versions[instance_id] = current_version
            return instance

    @staticmethod
    def get(instance_id: UUID) -> AdapterInstance:
        """Get an adapter instance by ID, returning the Pydantic model."""
        with get_session() as session:
            row = session.get(AdapterInstanceDB, instance_id)

        if not row:
            raise KeyError(f"Adapter instance {instance_id} not found")

        return AdapterInstance(
            id=row.id,
            adapter_name=row.adapter_name,
            identifier=row.identifier,
        )

    @staticmethod
    def create(instance_create: AdapterInstanceCreate) -> AdapterInstance:
        with get_session() as session:
            db_obj = AdapterInstanceDB(
                adapter_name=instance_create.adapter_name,
                identifier=instance_create.identifier,
            )
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)

        # instance_object = AdapterService.create_instance(
        #    db_obj.adapter_name, db_obj.identifier
        # )
        # AdapterInstanceService.instance_objects[db_obj.id] = instance_object
        logger.info(
            f"Created adapter instance: {instance_create.adapter_name}.{instance_create.identifier}"
        )
        return AdapterInstance(
            id=db_obj.id,
            adapter_name=db_obj.adapter_name,
            identifier=db_obj.identifier,
        )

    @staticmethod
    def list(filter: AdapterInstanceListFilter) -> Page[AdapterInstance]:
        with get_session() as session:
            q = select(AdapterInstanceDB)
            if filter:
                if filter.adapter_name is not None:
                    q = q.where(AdapterInstanceDB.adapter_name == filter.adapter_name)
                if filter.identifier is not None:
                    q = q.where(AdapterInstanceDB.identifier == filter.identifier)

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            q = q.order_by(AdapterInstanceDB.adapter_name, AdapterInstanceDB.identifier)
            if filter and filter.offset is not None:
                q = q.offset(filter.offset)
            if filter and filter.limit is not None:
                q = q.limit(apply_page_limit(filter.limit))
            rows = session.exec(q).all()
            items = [
                AdapterInstance(
                    id=i.id, adapter_name=i.adapter_name, identifier=i.identifier
                )
                for i in rows
            ]

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @staticmethod
    def delete(adapter_name: str, identifier: str) -> None:
        with get_session() as session:
            instance_record = session.exec(
                select(AdapterInstanceDB).where(
                    (AdapterInstanceDB.adapter_name == adapter_name)
                    & (AdapterInstanceDB.identifier == identifier)
                )
            ).first()

            if not instance_record:
                raise ValueError("Not found")

            instance_id = instance_record.id
            session.delete(instance_record)
            session.commit()

        AdapterInstanceService.instance_objects.pop(instance_id, None)

        logger.info(f"Deleted adapter instance: {adapter_name}.{identifier}")

    @staticmethod
    def get_config(name, identifier):
        obj = AdapterService.get_clsobj_by_name(name)
        _, adapter_inst_config_type = get_adapter_config_types(obj)
        return ConfigService(f"{name}.{identifier}", adapter_inst_config_type).get()

    @staticmethod
    def set_config(name: str, identifier: str, config_data: dict[str, Any]) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        _, adapter_inst_config_type = get_adapter_config_types(obj)
        try:
            config_model = adapter_inst_config_type.model_validate(config_data)
        except ValidationError as e:
            logger.warning(
                f"Failed to validate adapter instance config for {name}.{identifier} when setting: {e}"
            )
            raise

        ConfigService(f"{name}.{identifier}", adapter_inst_config_type).set(
            config_model
        )
        return config_model.model_dump()
