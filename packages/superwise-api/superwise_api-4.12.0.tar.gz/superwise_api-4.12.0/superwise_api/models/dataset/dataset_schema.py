from enum import Enum
from typing import Any
from typing import Optional

from pydantic import BaseModel

from superwise_api.models import SuperwiseEntity


class SchemaItemType(str, Enum):
    NUMERIC = "numeric"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"


class SchemaItem(SuperwiseEntity):
    type: SchemaItemType
    default_value: Any = None


class DatasetSchema(SuperwiseEntity):
    """
    DatasetSchema
    """

    fields: Optional[dict[str, SchemaItem]] = {}
    key_field: Optional[str] = None
    __properties = ["fields", "key_field"]

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[DatasetSchema]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return DatasetSchema.model_validate(obj)

        _obj = DatasetSchema.model_validate(
            {
                "key_field": obj.get("key_field"),
                "timestamp_partition_field": obj.get("timestamp_partition_field"),
                "fields": obj.get("fields"),
            }
        )
        return _obj


class RecordLogMessage(BaseModel):
    record: dict
