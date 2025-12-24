from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from superwise_api.models import SuperwiseEntity
from superwise_api.models.agent.agent import OpenAIModel, OpenAICompatibleModel


class GuardruleType(str, Enum):
    """Enumeration of all available guard types."""

    TOXICITY = "toxicity"
    ALLOWED_TOPICS = "allowed_topics"
    RESTRICTED_TOPICS = "restricted_topics"
    CORRECT_LANGUAGE = "correct_language"
    STRING_CHECK = "string_check"
    COMPETITOR_CHECK = "competitor_check"
    PII_DETECTION = "pii_detection"
    DETECT_JAILBREAK = "detect_jailbreak"


class BaseGuardrule(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(default="", min_length=1, max_length=100)
    tags: set[Literal["input", "output"]] = Field(default_factory=set)


GuardModelLLM = Annotated[
    Union[OpenAIModel, OpenAICompatibleModel],
    Field(..., discriminator="provider"),
]


class AllowedTopicsGuard(BaseGuardrule):
    topics: list[str]
    type: Literal[GuardruleType.ALLOWED_TOPICS.value] = Field(default=GuardruleType.ALLOWED_TOPICS.value)
    model: GuardModelLLM


class RestrictedTopicsGuard(BaseGuardrule):
    topics: list[str]
    type: Literal[GuardruleType.RESTRICTED_TOPICS.value] = Field(default=GuardruleType.RESTRICTED_TOPICS.value)
    model: GuardModelLLM


class ToxicityGuard(BaseGuardrule):
    type: Literal[GuardruleType.TOXICITY.value] = Field(default=GuardruleType.TOXICITY.value)
    threshold: float = 0.5
    validation_method: Literal["sentence"] | Literal["full"] = "sentence"


class CorrectLanguageGuard(BaseGuardrule):
    type: Literal[GuardruleType.CORRECT_LANGUAGE.value] = Field(default=GuardruleType.CORRECT_LANGUAGE.value)
    language_codes: list[str] = Field(default_factory=list)
    filter_mode: Literal["include"] | Literal["exclude"] = "include"


class StringCheckGuard(BaseGuardrule):
    type: Literal[GuardruleType.STRING_CHECK.value] = Field(default=GuardruleType.STRING_CHECK.value)
    regex_pattern: set[str] = Field(default_factory=set)


class CompetitorCheckGuard(BaseGuardrule):
    type: Literal[GuardruleType.COMPETITOR_CHECK.value] = Field(default=GuardruleType.COMPETITOR_CHECK.value)
    competitor_names: set[str] = Field(default_factory=set)


class PiiDetectionGuard(BaseGuardrule):
    type: Literal[GuardruleType.PII_DETECTION.value] = Field(default=GuardruleType.PII_DETECTION.value)
    threshold: float = Field(default=0.5)
    categories: set[str] = Field(default_factory=set)


class DetectJailbreakGuard(BaseGuardrule):
    type: Literal[GuardruleType.DETECT_JAILBREAK.value] = Field(default=GuardruleType.DETECT_JAILBREAK.value)
    tags: set[Literal["input"]] = Field(default_factory=set)
    threshold: float = Field(default=0.7)


Guardrule = Annotated[
    Union[
        ToxicityGuard,
        AllowedTopicsGuard,
        RestrictedTopicsGuard,
        CorrectLanguageGuard,
        StringCheckGuard,
        CompetitorCheckGuard,
        PiiDetectionGuard,
        DetectJailbreakGuard,
    ],
    Field(discriminator="type"),
]
GuardRules = list[Guardrule]


class GuardrailVersion(SuperwiseEntity):
    id: UUID
    guardrail_id: UUID
    name: str = Field(..., min_length=1, max_length=95)
    description: str | None = Field(None, max_length=100)
    guardrules: GuardRules = Field(default_factory=list)
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        return GuardrailVersion.model_validate(obj)


class Guardrail(SuperwiseEntity):
    id: UUID
    name: str = Field(..., min_length=1, max_length=95)
    description: str | None = Field(None, max_length=100)
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    current_version: GuardrailVersion | None = None
    tags: list[UUID] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        return Guardrail.model_validate(obj)


class GuardrailValidationResponse(BaseModel):
    id: Optional[UUID] = None
    name: str
    type: Literal[
        GuardruleType.ALLOWED_TOPICS.value,
        GuardruleType.COMPETITOR_CHECK.value,
        GuardruleType.CORRECT_LANGUAGE.value,
        GuardruleType.DETECT_JAILBREAK.value,
        GuardruleType.PII_DETECTION.value,
        GuardruleType.RESTRICTED_TOPICS.value,
        GuardruleType.STRING_CHECK.value,
        GuardruleType.TOXICITY.value,
    ]
    valid: bool
    message: str

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        return GuardrailValidationResponse.model_validate(obj)


GuardrailValidationResponses = list[GuardrailValidationResponse]
