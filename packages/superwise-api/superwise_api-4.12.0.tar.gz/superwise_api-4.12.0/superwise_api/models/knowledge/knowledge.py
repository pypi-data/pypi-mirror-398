from datetime import datetime
from typing import Optional

from pydantic import Field
from pydantic import TypeAdapter
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity
from superwise_api.models.tool.tool import EmbeddingModel
from superwise_api.models.tool.tool import KnowledgeMetadata


class Knowledge(SuperwiseEntity):
    id: UUID4
    name: str = Field(..., min_length=1, max_length=50)
    knowledge_metadata: KnowledgeMetadata
    embedding_model: EmbeddingModel
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    indexed_at: datetime | None = None

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[Knowledge]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Knowledge.model_validate(obj)

        _obj = Knowledge.model_validate(
            {
                "id": obj.get("id"),
                "name": obj.get("name"),
                "knowledge_metadata": TypeAdapter(KnowledgeMetadata).validate_python(obj.get("knowledge_metadata")),
                "embedding_model": obj.get("embedding_model"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "created_by": obj.get("created_by"),
                "indexed_at": obj.get("indexed_at"),
            }
        )
        return _obj
