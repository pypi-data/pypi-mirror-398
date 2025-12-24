from datetime import datetime
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field

from superwise_api.models import SuperwiseEntity


class Empty(BaseModel): ...


class IntermediateStep(BaseModel):
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime = Field(default_factory=datetime.utcnow)
    input_data: Optional[str]
    output_data: Optional[str]


class DebugMetadata(BaseModel):
    question: str
    answer: str
    start_time: datetime
    end_time: datetime
    intermediate_steps: list[IntermediateStep]


class ResponseMetadata(BaseModel):
    cite_sources: Optional[list[Optional[str]]] = Field(default=None, description="The sources cited in the response.")
    debug_metadata: Optional[DebugMetadata] = Field(
        default=None, description="Debug metadata associated with the response if applicable."
    )


class AskResponsePayload(SuperwiseEntity):
    output: str = Field(..., description="The AI agent's response to the user's inquiry.")
    metadata: Union[ResponseMetadata, Empty] = Field(
        default=Empty(), description="The metadata associated with the response."
    )

    @classmethod
    def from_dict(cls, data: dict) -> "AskResponsePayload":
        metadata = data.get("metadata")
        if metadata:
            data["metadata"] = ResponseMetadata(**metadata)
        return cls(**data)
