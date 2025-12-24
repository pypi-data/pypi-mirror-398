from datetime import datetime

from pydantic import Field, ConfigDict
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity


class TagCreatePayload(SuperwiseEntity):
    name: str = Field(..., min_length=1, max_length=50)
    color: str


class Tag(TagCreatePayload):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
