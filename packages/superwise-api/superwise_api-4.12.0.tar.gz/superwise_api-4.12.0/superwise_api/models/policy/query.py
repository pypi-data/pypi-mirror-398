from typing import Any
from typing import Optional
from typing import Union

from pydantic import BaseModel

from superwise_api.models import SuperwiseEntity


class Filter(BaseModel):
    member: str
    operator: str
    values: Optional[list[str]]


class Order(BaseModel):
    id: str
    desc: bool


class Query(SuperwiseEntity):
    measures: Optional[list[str]] = None
    order: Optional[Union[list[Order], Order]] = None
    dimensions: list[str] = None
    timezone: Optional[str] = "UTC"
    filters: list[Filter] = None
    timeDimensions: Optional[list[dict[str, Any]]] = None
    limit: Optional[int] = None

    def to_dict(self):
        return self.model_dump(exclude_none=True)
