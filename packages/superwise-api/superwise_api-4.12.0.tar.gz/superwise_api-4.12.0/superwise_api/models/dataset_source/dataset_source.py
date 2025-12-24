from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import ConfigDict
from pydantic import Field

from superwise_api.models import SuperwiseEntity


class IngestType(str, Enum):
    INSERT = "insert"
    UPDATE = "update"


class DatasetSource(SuperwiseEntity):
    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: UUID
    source_id: UUID = Field(alias="source_id")
    dataset_id: str = Field(alias="internal_dataset_id")
    folder: str | None = Field()
    query: str | None = Field()
    created_at: datetime | None = Field()
    updated_at: datetime | None = Field()
    created_by: str = Field()
    ingest_type: IngestType = Field(default=IngestType.INSERT)

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[DatasetSource]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return DatasetSource.model_validate(obj)

        _obj = DatasetSource.model_validate(
            {
                "id": obj.get("id"),
                "source_id": obj.get("source_id"),
                "internal_dataset_id": obj.get("internal_dataset_id")
                if obj.get("internal_dataset_id")
                else obj.get("dataset_id"),
                "folder": obj.get("folder"),
                "query": obj.get("query"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "created_by": obj.get("created_by"),
                "ingest_type": obj.get("ingest_type"),
            }
        )
        return _obj
