from datetime import datetime
from uuid import UUID

from loguru import logger
from pushikoo_interface import Detail, Struct, StructImage, StructText
from sqlmodel import func, select

from pushikoo.db import Message as MessageDB
from pushikoo.db import get_session
from pushikoo.model.message import (
    Message,
    MessageCreate,
    MessageListFilter,
    MessageOrder,
    MessageUpdate,
)
from pushikoo.model.pagination import Page, apply_page_limit


class MessageService:
    @staticmethod
    def create(message_create: MessageCreate) -> Message:
        with get_session() as session:
            db_obj = MessageDB(
                message_identifier=message_create.message_identifier,
                getter_name=message_create.getter_name,
                ts=message_create.ts,
                content=message_create.content.model_dump(),
            )
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        logger.info(
            f"Created message: {message_create.message_identifier} from {message_create.getter_name}"
        )
        return Message(
            id=db_obj.id,
            message_identifier=message_create.message_identifier,
            getter_name=message_create.getter_name,
            ts=message_create.ts,
            content=message_create.content,
        )

    @staticmethod
    def _extract_text_from_struct(struct: Struct) -> str:
        """Extract all text content from a Struct for keyword searching."""
        text_parts = []
        if struct and struct.content:
            for item in struct.content:
                # Extract text from StructText items (type='text' or type='title')
                if hasattr(item, "type") and item.type in ("text", "title"):
                    if hasattr(item, "text") and item.text:
                        text_parts.append(item.text)
        return " ".join(text_parts)

    @staticmethod
    def list(filter: MessageListFilter) -> Page[Message]:
        with get_session() as session:
            # Build base query for filtering
            q = select(MessageDB)
            if filter:
                if filter.getter_name is not None:
                    q = q.where(MessageDB.getter_name == filter.getter_name)
                if filter.message_identifier is not None:
                    q = q.where(
                        MessageDB.message_identifier == filter.message_identifier
                    )
                if filter.ts_from is not None:
                    q = q.where(MessageDB.ts >= filter.ts_from)
                if filter.ts_to is not None:
                    q = q.where(MessageDB.ts <= filter.ts_to)

            # Apply ordering
            if filter:
                if filter.order == MessageOrder.TS_ASC:
                    q = q.order_by(MessageDB.ts.asc())
                elif filter.order == MessageOrder.TS_DESC:
                    q = q.order_by(MessageDB.ts.desc())
                elif filter.order == MessageOrder.IDENTIFIER_ASC:
                    q = q.order_by(MessageDB.message_identifier.asc())
                elif filter.order == MessageOrder.IDENTIFIER_DESC:
                    q = q.order_by(MessageDB.message_identifier.desc())
                elif filter.order == MessageOrder.GETTER_NAME_ASC:
                    q = q.order_by(MessageDB.getter_name.asc(), MessageDB.ts.desc())
                elif filter.order == MessageOrder.GETTER_NAME_DESC:
                    q = q.order_by(MessageDB.getter_name.desc(), MessageDB.ts.desc())
                else:
                    q = q.order_by(MessageDB.ts.desc())

            # If keywords provided, fetch all and filter in memory, then paginate
            if filter and filter.keywords:
                keywords = [kw.lower() for kw in filter.keywords.split() if kw.strip()]

                if keywords:
                    # Fetch all matching rows (no pagination yet)
                    rows = session.exec(q).all()
                    all_items = [
                        Message(
                            id=m.id,
                            message_identifier=m.message_identifier,
                            getter_name=m.getter_name,
                            ts=m.ts,
                            content=Struct.model_validate(m.content),
                        )
                        for m in rows
                    ]

                    # Filter by keywords
                    filtered_items = []
                    for item in all_items:
                        text_content = MessageService._extract_text_from_struct(
                            item.content
                        )
                        text_lower = text_content.lower()
                        if all(keyword in text_lower for keyword in keywords):
                            filtered_items.append(item)

                    # Get total after keyword filtering
                    total = len(filtered_items)

                    # Apply pagination manually
                    offset = filter.offset or 0
                    limit = apply_page_limit(filter.limit) if filter.limit else None
                    if limit:
                        items = filtered_items[offset : offset + limit]
                    else:
                        items = filtered_items[offset:]

                    return Page(
                        items=items,
                        total=total,
                        limit=filter.limit if filter else None,
                        offset=filter.offset if filter else None,
                    )

            # No keywords: use normal DB pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            if filter:
                if filter.offset is not None:
                    q = q.offset(filter.offset)
                if filter.limit is not None:
                    q = q.limit(apply_page_limit(filter.limit))

            rows = session.exec(q).all()
            items = [
                Message(
                    id=m.id,
                    message_identifier=m.message_identifier,
                    getter_name=m.getter_name,
                    ts=m.ts,
                    content=Struct.model_validate(m.content),
                )
                for m in rows
            ]

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @staticmethod
    def exists(getter_name: str, message_identifier: str) -> bool:
        with get_session() as session:
            q = (
                select(MessageDB.id)
                .where(
                    (MessageDB.message_identifier == message_identifier)
                    & (MessageDB.getter_name == getter_name)
                )
                .limit(1)
            )
            return session.exec(q).first() is not None

    @staticmethod
    def get(message_id: UUID) -> Message:
        with get_session() as session:
            m = session.exec(select(MessageDB).where(MessageDB.id == message_id)).one()
        return Message(
            id=m.id,
            message_identifier=m.message_identifier,
            getter_name=m.getter_name,
            ts=m.ts,
            content=Struct.model_validate(m.content),
        )

    @staticmethod
    def delete(message_id: UUID) -> None:
        with get_session() as session:
            message_record = session.exec(
                select(MessageDB).where(MessageDB.id == message_id)
            ).first()

            if not message_record:
                raise ValueError("Not found")

            session.delete(message_record)
            session.commit()
        logger.info(f"Deleted message: {message_id}")

    @staticmethod
    def update(message_id: UUID, message_update: MessageUpdate) -> Message:
        update_data = {}
        if message_update.message_identifier is not None:
            update_data["message_identifier"] = message_update.message_identifier
        if message_update.getter_name is not None:
            update_data["getter_name"] = message_update.getter_name
        if message_update.ts is not None:
            update_data["ts"] = message_update.ts
        if message_update.content is not None:
            update_data["content"] = (
                message_update.content.model_dump()
                if hasattr(message_update.content, "model_dump")
                else message_update.content
            )

        with get_session() as session:
            obj = session.exec(
                select(MessageDB).where(MessageDB.id == message_id)
            ).one()
            for k, v in update_data.items():
                setattr(obj, k, v)
            if update_data:
                session.add(obj)
                session.commit()
                session.refresh(obj)

            result = Message(
                id=obj.id,
                message_identifier=obj.message_identifier,
                getter_name=obj.getter_name,
                ts=obj.ts,
                content=Struct.model_validate(obj.content),
            )

        if update_data:
            logger.info(f"Updated message: {message_id}")
        return result

    class Template:
        @staticmethod
        def v1(detail: Detail) -> Struct:
            """
            This is the title.

            Content line 1.
            Content line 2.
            Content line n.

            Author · Time · detail_1 · ... · detail_n
            url_1
            ...
            url_n
            """

            result = Struct()

            # ---------- Time ----------
            time_str = datetime.fromtimestamp(detail.ts).strftime("%H:%M")

            # ---------- Title ----------
            if detail.title:
                result.append(StructText(text=f"{detail.title}\n\n"))

            # ---------- Content ----------
            content = detail.content
            if isinstance(content, Struct):
                result.extend(content)
            elif isinstance(content, str):
                text = content.rstrip("\n") + "\n"
                result.append(StructText(text=text))
            else:
                raise TypeError(f"Unsupported content type: {type(content)}")

            # ---------- Images ----------
            for img in detail.image:
                if isinstance(img, StructImage):
                    result.append(img)
                elif isinstance(img, str):
                    result.append(StructImage(source=img))
                elif isinstance(img, dict):
                    result.append(StructImage(**img))
                else:
                    raise TypeError(f"Unsupported image type: {type(img)}")

            # ---------- Meta line ----------
            meta_parts: list[str] = []

            if detail.author_name:
                meta_parts.append(detail.author_name)

            meta_parts.append(time_str)

            if isinstance(detail.extra_detail, list):
                meta_parts.extend(str(v) for v in detail.extra_detail if v)

            meta_text = " · ".join(meta_parts)

            meta_block = "\n" + meta_text if meta_text else ""

            # ---------- URLs ----------
            urls: list[str] = []
            if isinstance(detail.url, str):
                urls = [detail.url]
            elif isinstance(detail.url, list):
                urls = [u for u in detail.url if u]

            if urls:
                meta_block += "\n" + "\n".join(urls)

            if meta_block:
                result.append(StructText(text=meta_block))

            return result
