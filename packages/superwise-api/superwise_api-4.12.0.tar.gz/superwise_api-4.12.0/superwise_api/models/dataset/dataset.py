from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity
from superwise_api.models.dataset.dataset_schema import DatasetSchema


class DatasetTag(BaseModel):
    key: str
    value: str


class Dataset(SuperwiseEntity):
    model_config = ConfigDict(
        populate_by_name=True,
    )

    internal_id: str = Field(..., alias="_id")
    id: str = Field()
    name: str = Field(..., description="A descriptive name for this dataset")
    description: str | None = Field(description="Relevant information about the context of this dataset")
    model_version_id: str | None = Field()
    created_at: datetime | None = Field()
    updated_at: datetime | None = Field()
    created_by: str = Field()
    tags: list[DatasetTag] | None = Field(default=None)
    dataset_schema: DatasetSchema = Field(alias="schema", default={})
    tenant_id: str | None
    tag_ids: list[UUID4] = Field(default_factory=list)

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.model_dump(by_alias=True, exclude={}, exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of var_schema
        if self.dataset_schema:
            _dict["schema"] = self.dataset_schema.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[Dataset]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Dataset.model_validate(obj)

        _obj = Dataset.model_validate(
            {
                "_id": obj.get("internal_id") if obj.get("internal_id") else obj.get("_id"),
                "id": obj.get("id"),
                "name": obj.get("name"),
                "description": obj.get("description"),
                "model_version_id": obj.get("model_version_id"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "created_by": obj.get("created_by"),
                "tenant_id": obj.get("tenant_id"),
                "tag_ids": obj.get("tag_ids"),
                "dataset_schema": DatasetSchema.from_dict(obj.get("schema"))
                if obj.get("schema")
                else obj.get("dataset_schema"),
            }
        )
        return _obj
