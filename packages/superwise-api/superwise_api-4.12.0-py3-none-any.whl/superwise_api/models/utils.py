from typing import Any, Literal

from pydantic import Field
from superwise_api.models import SuperwiseEntity


class SearchParams(SuperwiseEntity):
    filters: list[Any] | None = Field(
        None,
        description="Filter on db columns",
        examples=[
            ["name", "eq", "active"],
            [["id", "eq", "5c05dc9f-f04a-4ce8-9d57-2ec63ee76aac"], "and", ["description", "ilike", "Construction"]],
        ],
    )
    search: str | None = Field(None, description="Free text search on searchable fields")
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_direction: Literal["asc", "desc"] = Field("desc", description="Sort direction (ascending or descending)")
