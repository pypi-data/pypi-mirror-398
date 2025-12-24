from datetime import datetime
from enum import Enum
from typing import Dict
from typing import Optional
from uuid import UUID

from pydantic import Field

from superwise_api.models import SuperwiseEntity


class VisualizationType(str, Enum):
    TABLE = "table"
    LINE_GRAPH = "line_graph"
    BAR_PLOT = "bar_plot"
    TIME_SERIES = "time_series"
    HISTOGRAM = "histogram"
    QUERY_VALUE = "query_value"


class WidgetMeta(SuperwiseEntity):
    visualization_type: VisualizationType
    x_pos: int
    y_pos: int
    height: int = 0
    width: int = 0


class Dashboard(SuperwiseEntity):
    id: UUID
    name: str = Field(title="name", min_length=1, max_length=100)
    created_by: str = Field()
    created_at: datetime
    updated_at: datetime
    positions: Dict[UUID, WidgetMeta]
    tags: list[UUID] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[Dashboard]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Dashboard.model_validate(obj)

        _obj = Dashboard.model_validate(
            {
                "id": obj.get("id"),
                "name": obj.get("name"),
                "created_by": obj.get("created_by"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "tags": obj.get("tags"),
                "positions": {k: WidgetMeta.model_validate(v) for k, v in obj.get("positions", {}).items()},
            }
        )
        return _obj
