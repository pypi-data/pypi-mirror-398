from uuid import UUID

from loguru import logger
from pushikoo_interface import Pusher, Struct
from sqlmodel import func, select

from pushikoo.db import AdapterInstance as AdapterInstanceDB
from pushikoo.db import WarningRecipient as WarningRecipientDB
from pushikoo.db import get_session
from pushikoo.model.adapter import AdapterInstance
from pushikoo.model.pagination import Page, apply_page_limit
from pushikoo.service.adapter import AdapterInstanceService, AdapterService


class WarningService:
    @staticmethod
    def add_recipient(adapter_instance_id: UUID) -> AdapterInstance:
        with get_session() as session:
            adapter_instance = session.exec(
                select(AdapterInstanceDB).where(
                    AdapterInstanceDB.id == adapter_instance_id
                )
            ).first()

            if not adapter_instance:
                raise KeyError(f"Adapter instance {adapter_instance_id} not found")

            # Check if the adapter is a Pusher
            adapter_class = AdapterService.get_clsobj_by_name(
                adapter_instance.adapter_name
            )
            if not issubclass(adapter_class, Pusher):
                raise ValueError(
                    f"Adapter {adapter_instance.adapter_name} is not a Pusher. "
                    "Only Pusher adapters can be warning recipients."
                )

            existing = session.exec(
                select(WarningRecipientDB).where(
                    WarningRecipientDB.adapter_instance_id == adapter_instance_id
                )
            ).first()

            if existing:
                raise FileExistsError(
                    f"Adapter instance {adapter_instance_id} already exists as warning recipient"
                )

            recipient = WarningRecipientDB(adapter_instance_id=adapter_instance_id)
            session.add(recipient)
            session.commit()
            result = AdapterInstance(
                id=adapter_instance.id,
                adapter_name=adapter_instance.adapter_name,
                identifier=adapter_instance.identifier,
            )
            logger.info(
                f"Added warning recipient for adapter instance {adapter_instance_id}"
            )
            return result

    @staticmethod
    def remove_recipient(adapter_instance_id: UUID) -> None:
        with get_session() as session:
            adapter_instance = session.exec(
                select(AdapterInstanceDB).where(
                    AdapterInstanceDB.id == adapter_instance_id
                )
            ).first()

            if not adapter_instance:
                raise KeyError(f"Adapter instance {adapter_instance_id} not found")

            recipient = session.exec(
                select(WarningRecipientDB).where(
                    WarningRecipientDB.adapter_instance_id == adapter_instance_id
                )
            ).first()

            if not recipient:
                raise LookupError(
                    f"Warning recipient for adapter instance {adapter_instance_id} not found"
                )

            session.delete(recipient)
            session.commit()
            logger.info(
                f"Removed warning recipient for adapter instance {adapter_instance_id}"
            )

    @staticmethod
    def list_recipients(
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[AdapterInstance]:
        with get_session() as session:
            q = (
                select(WarningRecipientDB)
                .join(AdapterInstanceDB)
                .order_by(WarningRecipientDB.created_at.desc())
            )

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            if offset is not None:
                q = q.offset(offset)
            if limit is not None:
                q = q.limit(apply_page_limit(limit))
            recipients = session.exec(q).all()
            items = [
                AdapterInstance(
                    id=r.adapter_instance.id,
                    adapter_name=r.adapter_instance.adapter_name,
                    identifier=r.adapter_instance.identifier,
                )
                for r in recipients
            ]

            return Page(
                items=items,
                total=total,
                limit=limit,
                offset=offset,
            )

    @staticmethod
    def issue(message: Struct) -> None:
        with get_session() as session:
            recipients = session.exec(select(WarningRecipientDB)).all()

            if not recipients:
                logger.warning("No warning recipients configured")
                return

            for recipient in recipients:
                try:
                    pusher_instance_object: Pusher = (
                        AdapterInstanceService.get_object_by_id(
                            recipient.adapter_instance_id
                        )
                    )
                    pusher_instance_object.push(message)
                    logger.debug(
                        f"Warning sent to adapter instance {recipient.adapter_instance_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send warning to adapter instance {recipient.adapter_instance_id}: {e}"
                    )
