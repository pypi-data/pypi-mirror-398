from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity
from superwise_api.models.dataset.dataset import Dataset


class Model(SuperwiseEntity):
    id: str
    internal_id: UUID4 = Field(alias="_id")
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
    )

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.model_dump(by_alias=True, exclude={}, exclude_none=True)
        _dict["_id"] = str(_dict["_id"])
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[Model]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Model.model_validate(obj)

        _obj = Model.model_validate(
            {
                "_id": obj.get("internal_id"),
                "id": obj.get("id"),
                "name": obj.get("name"),
                "description": obj.get("description"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "created_by": obj.get("created_by"),
            }
        )
        return _obj


class ModelExtended(Model):
    datasets: list[Dataset]

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[ModelExtended]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return ModelExtended.model_validate(obj)

        _obj = ModelExtended.model_validate(
            {
                "_id": obj.get("_id"),
                "id": obj.get("id"),
                "name": obj.get("name"),
                "description": obj.get("description"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "created_by": obj.get("created_by"),
                "datasets": [Dataset.from_dict(dataset) for dataset in obj.get("datasets")],
            }
        )
        return _obj
