from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class IntegrationType(str, Enum):
    SLACK = "slack"


class Integration(BaseModel):
    id: UUID
    integration_type: IntegrationType
    updated_at: datetime
    created_at: datetime
    created_by: str
    tenant_id: str

    @classmethod
    def from_dict(cls, dict_: dict) -> "Integration":
        return Integration(**dict_)
