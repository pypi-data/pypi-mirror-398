from datetime import datetime
from enum import Enum
from typing import Dict
from typing import Literal
from typing import Optional
from typing import Union
from uuid import UUID

from pydantic import Field

from superwise_api.models import SuperwiseEntity
from superwise_api.models.dashboard.dashboard import VisualizationType
from superwise_api.models.dashboard.query import Query


class DataConfigType(str, Enum):
    GENERAL = "general"
    DISTRIBUTION_COMPARE = "distribution_compare"


class DistanceFunction(str, Enum):
    WASSERSTEIN_DISTANCE = "wasserstein_distance"
    JENSEN_SHANNON_DIVERGENCE = "jensen_shannon_divergence"


class DataConfigBase(SuperwiseEntity):
    type: DataConfigType


class DataConfigGeneral(DataConfigBase):
    type: Literal[DataConfigType.GENERAL] = DataConfigType.GENERAL
    query: Query


class DataConfigDistributionCompare(DataConfigBase):
    type: Literal[DataConfigType.DISTRIBUTION_COMPARE] = DataConfigType.DISTRIBUTION_COMPARE
    query_a: Query
    query_b: Query
    distance_function: Optional[DistanceFunction] = None


class Datasource(str, Enum):
    DATASETS = "datasets"
    EVENTS = "events"


class QueryType(str, Enum):
    RAW_DATA = "raw_data"
    STATISTICS = "statistics"
    TIME_SERIES = "time_series"
    DISTRIBUTION = "distribution"


DATA_CONFIG = DataConfigGeneral | DataConfigDistributionCompare


class DashboardItem(SuperwiseEntity):
    id: UUID
    name: str = Field(title="name", min_length=1, max_length=50)
    query_type: QueryType
    datasource: Datasource
    visualization_type: VisualizationType | None = None
    data_config: DATA_CONFIG
    created_by: str = Field()
    created_at: datetime
    updated_at: datetime
    dashboard_id: UUID
    item_metadata: Dict[str, Union[str, Dict[str, str]]]

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[DashboardItem]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return DashboardItem.model_validate(obj)

        data_config_type = obj["data_config"]["type"]
        if data_config_type == DataConfigType.GENERAL:
            obj["data_config"] = DataConfigGeneral(**obj["data_config"])
        elif data_config_type == DataConfigType.DISTRIBUTION_COMPARE:
            obj["data_config"] = DataConfigDistributionCompare(**obj["data_config"])
        else:
            raise ValueError(f"Unknown data_config type: {data_config_type}")

        _obj = DashboardItem.model_validate(
            {
                "id": obj.get("id"),
                "name": obj.get("name"),
                "query_type": QueryType(obj.get("query_type")),
                "datasource": Datasource(obj.get("datasource")),
                "data_config": obj.get("data_config"),
                "created_by": obj.get("created_by"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "dashboard_id": obj.get("dashboard_id"),
                "item_metadata": obj.get("item_metadata"),
            }
        )
        return _obj
