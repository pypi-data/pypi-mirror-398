import datetime
import uuid
from typing import Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlalchemy_utc import UtcDateTime
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

from pushikoo.util.db import JSONField
from pushikoo.util.setting import DATA_DIR


DB_PATH = DATA_DIR / "pushikoo.db"
engine = create_engine(
    f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False}
)


def get_session() -> Session:
    return Session(engine)


class AdapterInstance(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("adapter_name", "identifier", name="uix_adapter_identifier"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    adapter_name: str
    identifier: str


class FlowCron(SQLModel, table=True):
    __tablename__ = "flowcron"
    __table_args__ = (UniqueConstraint("flow_id", "cron", name="uix_flow_cron"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    flow_id: uuid.UUID = Field(foreign_key="flow.id")
    cron: str
    enabled: bool = True

    # relationship
    flow: "Flow" = Relationship()


class Flow(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = ""
    # JSON list of adapter_instance_id (UUID as string in storage)
    nodes: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONField),
    )


class FlowInstance(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    flow_id: uuid.UUID = Field(foreign_key="flow.id")
    status: str
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(UtcDateTime()),
    )


class Message(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "message_identifier", "getter_name", name="uix_message_identifier_getter"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    message_identifier: str
    getter_name: str
    ts: float
    content: dict = Field(sa_column=Column(JSON))


class Config(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class WarningRecipient(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("adapter_instance_id", name="uix_warning_recipient"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    adapter_instance_id: uuid.UUID = Field(foreign_key="adapterinstance.id")
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(UtcDateTime()),
    )

    # relationships
    adapter_instance: AdapterInstance = Relationship()


class PipIndex(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("url", name="uix_pip_index"),)

    url: str = Field(primary_key=True)


class File(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    path: str
    mime: Optional[str] = None


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


__all__ = [
    # base
    "engine",
    "get_session",
    "init_db",
    # adapter
    "AdapterInstance",
    "Flow",
    "FlowCron",
    "FlowInstance",
    # message
    "Message",
    # config/files
    "Config",
    "File",
    # warning
    "WarningRecipient",
    # pip
    "PipIndex",
]
