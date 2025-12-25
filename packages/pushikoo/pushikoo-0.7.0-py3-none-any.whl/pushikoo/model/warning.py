from uuid import UUID

from pydantic import BaseModel


class WarningRecipientCreate(BaseModel):
    adapter_instance_id: UUID
