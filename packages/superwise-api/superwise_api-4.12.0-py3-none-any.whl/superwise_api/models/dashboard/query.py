from enum import Enum
from typing import Any
from typing import Optional
from typing import Union

from pydantic import BaseModel

from superwise_api.models import SuperwiseEntity


class Granularity(str, Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class Filter(BaseModel):
    member: str
    operator: str
    values: Optional[Union[list[str], None]]


class TimeDimension(BaseModel):
    dimension: str
    granularity: Granularity


class Query(SuperwiseEntity):
    measures: list[str]
    order: Optional[Union[list[tuple], tuple]] = []
    dimensions: list[str] = []
    timezone: Optional[str] = "UTC"
    filters: list[Filter] = []
    limit: Optional[int] = 10000
    timeDimensions: Optional[list[dict[str, Any]]] = []

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Query.model_validate(obj)

        _obj = Query.model_validate(
            {
                "measures": obj.get("measures"),
                "order": obj.get("order"),
                "dimensions": obj.get("dimensions"),
                "timezone": obj.get("timezone"),
                "filters": obj.get("filters"),
                "limit": obj.get("limit"),
                "timeDimensions": obj.get("timeDimensions")
                if obj.get("timeDimensions")
                else obj.get("time_dimensions"),
            }
        )
        return _obj
