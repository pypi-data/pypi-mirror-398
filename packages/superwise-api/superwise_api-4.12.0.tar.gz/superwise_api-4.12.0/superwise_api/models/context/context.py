from pydantic import BaseModel
from pydantic import Field

from superwise_api.models.tool.tool import ContextConfig


class ContextDef(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    config: ContextConfig
