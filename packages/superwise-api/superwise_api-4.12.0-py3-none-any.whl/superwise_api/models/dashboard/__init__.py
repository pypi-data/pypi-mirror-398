from datetime import datetime
from typing import Optional

from pydantic import Field

from superwise_api.models import SuperwiseEntity


class DashboardItem(SuperwiseEntity):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    query_type: str
    datasource: str
    query: dict
    created_by: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    dashboard_id: str
    item_metadata: dict

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Sales Widget",
                "query_type": "raw_data",
                "datasource": "sales_database",
                "query": {"select": "sum(sales)", "where": "region = 'West'"},
                "dashboard_id": "dashboard123",
                "item_metadata": {"color": "blue"},
            }
        }
    }
