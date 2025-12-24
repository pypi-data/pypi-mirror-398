from datetime import datetime
from uuid import UUID

from pydantic import field_serializer

from superwise_api.models import SuperwiseEntity


class SlackDestinationParams(SuperwiseEntity):
    channel_id: str

    def to_dict(self):
        return self.model_dump()


class Destination(SuperwiseEntity):
    id: UUID
    name: str
    integration_id: UUID
    params: SlackDestinationParams
    updated_at: datetime
    created_at: datetime
    created_by: str
    tenant_id: str

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    def to_dict(self) -> dict:
        dict_ = self.model_dump(exclude_none=True)
        return dict_

    @classmethod
    def from_dict(cls, dict_: dict) -> "Destination":
        dict_["params"] = SlackDestinationParams(**dict_["params"])
        return cls(**dict_)
