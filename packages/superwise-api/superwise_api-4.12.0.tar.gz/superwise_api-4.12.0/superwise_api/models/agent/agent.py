from datetime import datetime
from enum import Enum
from typing import Annotated
from typing import List
from typing import Literal
from typing import Optional
from typing import TypeAlias
from typing import Union

from pydantic import BaseModel
from pydantic import confloat
from pydantic import conint
from pydantic import Discriminator
from pydantic import Field
from pydantic import field_validator
from pydantic import HttpUrl
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity
from superwise_api.models.agent.flowise import FlowiseCredentialUserInput
from superwise_api.models.context.context import ContextDef
from superwise_api.models.tool.tool import ToolDef


class ModelProvider(str, Enum):
    OPENAI = "OpenAI"
    OPENAI_COMPATIBLE = "OpenAICompatible"
    GOOGLE = "GoogleAI"
    SUPERWISE = "Superwise"
    ANTHROPIC = "Anthropic"
    VERTEX_AI_MODEL_GARDEN = "VertexAIModelGarden"


class OpenAIModelVersion(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    CHATGPT_4O_LATEST = "chatgpt-4o-latest"
    O1 = "o1"
    O3_MINI = "o3-mini"


class GoogleModelVersion(str, Enum):
    GEMINI_2_0_FLASH = "models/gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "models/gemini-2.0-flash-lite"
    GEMINI_2_0_FLASH_EXP = "models/gemini-2.0-flash-exp"
    GEMINI_2_0_FLASH_THINKING_EXP = "models/gemini-2.0-flash-thinking-exp"
    GEMINI_2_5_FLASH = "models/gemini-2.5-flash"
    GEMINI_2_5_PRO = "models/gemini-2.5-pro"
    GEMINI_2_5_FLASH_LITE = "models/gemini-2.5-flash-lite"


class AnthropicModelVersion(str, Enum):
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-latest"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-latest"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-latest"
    CLAUDE_3_OPUS = "claude-3-opus-latest"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_SONNET_4 = "claude-sonnet-4-0"
    CLAUDE_OPUS_4 = "claude-opus-4-0"


class VertexAIModelGardenVersion(str, Enum):
    PLACEHOLDER = "placeholder"


class AgentStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"
    UPDATING = "updating"


class OpenAIParameters(BaseModel):
    temperature: confloat(ge=0, le=2) = 0
    top_p: confloat(ge=0, le=1) = 1
    max_tokens: Optional[conint(ge=1)] = None


class OpenAICompatibleParameters(OpenAIParameters):
    top_p: Optional[confloat(ge=0, le=1)] = None
    top_k: Optional[conint(ge=1)] = None


class GoogleParameters(BaseModel):
    temperature: confloat(ge=0, le=1) = 0
    top_p: confloat(ge=0, le=1) = 1
    top_k: conint(ge=1) = 40
    max_tokens: Optional[conint(ge=1)] = None


class AnthropicParameters(BaseModel):
    temperature: confloat(ge=0, le=1) = 0
    top_p: confloat(ge=0, le=1) = 1
    top_k: conint(ge=1) = 40
    max_tokens: Optional[conint(ge=1)] = None


class VertexAIModelGardenParameters(BaseModel):
    max_tokens: Optional[conint(ge=1)] = None


class BaseModelLLM(BaseModel):
    api_token: str

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return ModelLLM.model_validate(obj)

        _obj = ModelLLM.model_validate(
            {"provider": obj.get("provider"), "version": obj.get("version"), "api_token": obj.get("api_token")}
        )
        return _obj

    def to_dict(self):
        return self.model_dump()


class OpenAIModel(BaseModelLLM):
    provider: Literal[ModelProvider.OPENAI.value] = ModelProvider.OPENAI.value
    version: OpenAIModelVersion
    parameters: OpenAIParameters = Field(default_factory=OpenAIParameters)


class PrebuiltModel(BaseModel):
    provider: Literal[ModelProvider.SUPERWISE.value] = ModelProvider.SUPERWISE.value


class OpenAICompatibleModel(BaseModelLLM):
    provider: Literal[ModelProvider.OPENAI_COMPATIBLE.value] = ModelProvider.OPENAI_COMPATIBLE.value
    version: str
    parameters: OpenAICompatibleParameters = Field(default_factory=OpenAICompatibleParameters)
    base_url: str


class GoogleModel(BaseModelLLM):
    provider: Literal[ModelProvider.GOOGLE.value] = ModelProvider.GOOGLE.value
    version: GoogleModelVersion
    parameters: GoogleParameters = Field(default_factory=GoogleParameters)


class AnthropicModel(BaseModelLLM):
    provider: Literal[ModelProvider.ANTHROPIC.value] = ModelProvider.ANTHROPIC.value
    version: AnthropicModelVersion
    parameters: AnthropicParameters = Field(default_factory=AnthropicParameters)


class VertexAIModelGardenModel(BaseModelLLM):
    provider: Literal[ModelProvider.VERTEX_AI_MODEL_GARDEN.value] = ModelProvider.VERTEX_AI_MODEL_GARDEN.value
    version: VertexAIModelGardenVersion
    parameters: VertexAIModelGardenParameters = Field(default_factory=VertexAIModelGardenParameters)


ModelLLM = Annotated[
    Union[OpenAIModel, PrebuiltModel, OpenAICompatibleModel, GoogleModel, AnthropicModel, VertexAIModelGardenModel],
    Field(..., discriminator="provider"),
]


class Framework(str, Enum):
    SUPERWISE = "Superwise"
    FLOWISE = "Flowise"


class AgentType(str, Enum):
    REACT_AGENT = "ReactAgent"
    AI_ASSISTANT = "AIAssistant"
    BASIC_LLM = "BasicLLM"
    FLOWISE = "Flowise"


class SuperwiseConfig(SuperwiseEntity):
    framework: Literal[Framework.SUPERWISE.value] = Framework.SUPERWISE.value
    show_cites: bool = Field(default=False)
    llm_model: ModelLLM = Field(..., alias="model")
    prompt: str | None = Field(None)


class ReactAgentConfig(SuperwiseConfig):
    type: Literal[AgentType.REACT_AGENT.value] = AgentType.REACT_AGENT.value
    tools: List[ToolDef]


AdvancedAgentConfig: TypeAlias = ReactAgentConfig


class ContextChainConfig(SuperwiseConfig):
    type: Literal[AgentType.AI_ASSISTANT.value] = AgentType.AI_ASSISTANT.value
    context: Optional[ContextDef]


AIAssistantConfig: TypeAlias = ContextChainConfig


class BasicLLMConfig(SuperwiseConfig):
    type: Literal[AgentType.BASIC_LLM.value] = AgentType.BASIC_LLM.value


class FlowiseConfigBase(SuperwiseEntity):
    type: Literal[AgentType.FLOWISE.value] = AgentType.FLOWISE.value
    flow_id: str
    url: str
    api_key: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v:
            return v
        HttpUrl(v)
        return v


class FlowiseGetCredentialSchema(FlowiseConfigBase):
    pass


class FlowiseAppConfig(FlowiseConfigBase):
    flowise_credentials: FlowiseCredentialUserInput | None = None


AgentConfig = Annotated[
    ReactAgentConfig | ContextChainConfig | BasicLLMConfig | FlowiseAppConfig, Discriminator("type")
]


class Agent(SuperwiseEntity):
    id: UUID4
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    name: str = Field(..., min_length=1, max_length=95)
    description: str | None = Field(None, max_length=100)
    dataset_id: str
    block_guardrails_violations: bool
    guardrails_violation_message: str
    url: HttpUrl
    status: AgentStatus = AgentStatus.UNKNOWN
    api_token: UUID4 | None
    tags: list[UUID4] = Field(default_factory=list)


class ExtendedAgent(Agent):
    framework: Literal[tuple(framework.value for framework in Framework)] | None = None
    last_published: datetime | None = None


class Version(SuperwiseEntity):
    id: UUID4
    agent_id: UUID4
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    name: str = Field(..., min_length=1, max_length=95)
    description: str | None = Field(None, max_length=100)
    agent_config: AgentConfig
    guardrails: list[UUID4] = []

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        return Version.model_validate(obj)
