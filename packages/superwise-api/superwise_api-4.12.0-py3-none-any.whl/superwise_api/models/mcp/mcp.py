from datetime import datetime
from typing import Any

from pydantic import Field
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity


class MCPBase(SuperwiseEntity):
    name: str = Field(..., min_length=1, max_length=255, description="MCP name")
    url: str = Field(..., min_length=1, description="MCP server URL")
    headers: dict[str, str] | None = Field(None, description="Authentication headers")
    params: dict[str, str] | None = Field(None, description="Additional query parameters")


class MCPToolSchema(SuperwiseEntity):
    name: str
    description: str
    inputSchema: dict[str, Any]


class MCP(MCPBase):
    id: UUID4 = Field(..., description="MCP entity ID")
    created_by: str = Field(..., description="User ID")
    tool_schemas: dict[str, MCPToolSchema] = Field(..., description="Cached schemas from MCP server")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    deleted_at: datetime | None = Field(None, description="Soft delete timestamp")
