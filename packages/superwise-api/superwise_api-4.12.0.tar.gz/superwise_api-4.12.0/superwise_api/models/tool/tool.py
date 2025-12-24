from enum import Enum
from typing import Annotated
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import Discriminator
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic import UUID4
from superwise_api.models.mcp.mcp import MCPToolSchema


class ToolType(str, Enum):
    PINECONE = "Pinecone"
    PG_VECTOR = "PGVector"
    KNOWLEDGE = "Knowledge"
    SQL_DATABASE_POSTGRES = "PostgreSQL"
    SQL_DATABASE_BIGQUERY = "BigQuery"
    SQL_DATABASE_MYSQL = "MySQL"
    SQL_DATABASE_MSSQL = "MSSQL"
    SQL_DATABASE_ORACLE = "Oracle"
    OPENAPI = "OpenAPI"
    MCP = "MCP"


class EmbeddingModelProvider(str, Enum):
    VERTEX_AI_MODEL_GARDEN = "VertexAIModelGarden"
    OPEN_AI = "OpenAI"
    OPEN_AI_COMPATIBLE = "OpenAICompatible"
    GOOGLE_AI = "GoogleAI"


class OpenAIEmbeddingModelVersion(str, Enum):
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


class GoogleAIEmbeddingModelVersion(str, Enum):
    EMBEDDING_V1 = "models/embedding-001"
    TEXT_EMBEDDING_004 = "models/text-embedding-004"


class ToolConfigSQLMetadata(BaseModel):
    include_tables: Optional[list[str]] = None
    exclude_tables: Optional[list[str]] = None

    @model_validator(mode="before")
    def validate_include_or_exclude_tables(cls, values) -> "ToolConfigSQLMetadata":
        include_tables, exclude_tables = values.get("include_tables"), values.get("exclude_tables")
        if all([include_tables, exclude_tables]):
            raise ValueError("Both include_tables and exclude_tables cannot be provided")
        if not any([include_tables, exclude_tables]):
            raise ValueError("Either include_tables or exclude_tables should be provided")
        return values


class ToolConfigBase(BaseModel):
    type: ToolType


class ToolConfigSQLBase(ToolConfigBase):
    type: Literal[
        ToolType.SQL_DATABASE_POSTGRES,
        ToolType.SQL_DATABASE_BIGQUERY,
        ToolType.SQL_DATABASE_MYSQL,
        ToolType.SQL_DATABASE_MSSQL,
        ToolType.SQL_DATABASE_ORACLE,
    ]
    config_metadata: Optional[ToolConfigSQLMetadata] = Field(default=None)


class EmbeddingModelBase(BaseModel):
    provider: EmbeddingModelProvider


class VertexAIModelGardenEmbeddingModel(EmbeddingModelBase):
    provider: Literal[EmbeddingModelProvider.VERTEX_AI_MODEL_GARDEN] = (
        EmbeddingModelProvider.VERTEX_AI_MODEL_GARDEN.value
    )
    project_id: str
    endpoint_id: str
    location: str
    service_account: dict[str, str]


class OpenAIEmbeddingModel(EmbeddingModelBase):
    provider: Literal[EmbeddingModelProvider.OPEN_AI] = EmbeddingModelProvider.OPEN_AI.value
    version: OpenAIEmbeddingModelVersion
    api_key: str


class GoogleAIEmbeddingModel(EmbeddingModelBase):
    provider: Literal[EmbeddingModelProvider.GOOGLE_AI] = EmbeddingModelProvider.GOOGLE_AI.value
    version: GoogleAIEmbeddingModelVersion
    api_key: str


class OpenAICompatibleEmbeddingModel(EmbeddingModelBase):
    provider: Literal[EmbeddingModelProvider.OPEN_AI_COMPATIBLE] = EmbeddingModelProvider.OPEN_AI_COMPATIBLE.value
    version: str
    api_key: str
    base_url: str


EmbeddingModel = Annotated[
    OpenAIEmbeddingModel | OpenAICompatibleEmbeddingModel | GoogleAIEmbeddingModel | VertexAIModelGardenEmbeddingModel,
    Discriminator("provider"),
]


class ToolConfigSQLDatabasePostgres(ToolConfigSQLBase):
    type: Literal[ToolType.SQL_DATABASE_POSTGRES] = ToolType.SQL_DATABASE_POSTGRES.value
    connection_string: str = Field(pattern=r"^postgresql://")


class ToolConfigSQLDatabaseMySQL(ToolConfigSQLBase):
    type: Literal[ToolType.SQL_DATABASE_MYSQL] = ToolType.SQL_DATABASE_MYSQL.value
    connection_string: str = Field(pattern=r"^mysql://")


class ToolConfigSQLDatabaseMSSQL(ToolConfigSQLBase):
    type: Literal[ToolType.SQL_DATABASE_MSSQL] = ToolType.SQL_DATABASE_MSSQL.value
    connection_string: str = Field(pattern=r"^mssql://")


class ToolConfigSQLDatabaseOracle(ToolConfigSQLBase):
    type: Literal[ToolType.SQL_DATABASE_ORACLE] = ToolType.SQL_DATABASE_ORACLE.value
    connection_string: str = Field(pattern=r"^oracle://")


class ToolConfigBigQuery(ToolConfigSQLBase):
    type: Literal[ToolType.SQL_DATABASE_BIGQUERY] = ToolType.SQL_DATABASE_BIGQUERY.value
    project_id: str
    dataset_id: str
    service_account: dict[str, str]


class ToolConfigPGVector(ToolConfigBase):
    type: Literal[ToolType.PG_VECTOR] = ToolType.PG_VECTOR.value
    connection_string: str
    table_name: str
    db_schema: Optional[str] = None
    embedding_model: EmbeddingModel


class ToolConfigPineconeVectorDB(ToolConfigBase):
    type: Literal[ToolType.PINECONE] = ToolType.PINECONE.value
    api_key: str
    index_name: str
    embedding_model: EmbeddingModel


class BearerAuthenticationConfig(BaseModel):
    type: Literal["Bearer"]
    token: str


AuthenticationConfig = BearerAuthenticationConfig


class KnowledgeType(str, Enum):
    URL = "url"
    FILE = "file"


class UrlKnowledgeMetadata(BaseModel):
    type: Literal[KnowledgeType.URL] = KnowledgeType.URL.value
    url: str
    max_depth: int = Field(..., ge=1, le=5)

    @field_validator("url")
    def validate_url_scheme(cls, value):
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("URL must start with 'http' or 'https'")
        return value


class FileKnowledgeMetadata(BaseModel):
    type: Literal[KnowledgeType.FILE] = KnowledgeType.FILE.value
    file_ids: list[str] = []


KnowledgeMetadata = Annotated[
    UrlKnowledgeMetadata | FileKnowledgeMetadata,
    Discriminator("type"),
]


class SupportedContentType(str, Enum):
    PDF = "agent/pdf"
    TXT = "text/plain"


class UploadStatus(str, Enum):
    SUCCESS = "success"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    UPLOAD_FAILED = "upload_failed"


class FileInfo(BaseModel):
    filename: str
    content_type: SupportedContentType
    size: int
    id: UUID4

    @classmethod
    def from_dict(cls, obj: dict):
        return cls.model_validate(obj)


class FileUploadResponse(BaseModel):
    status: UploadStatus
    file_info: Optional[FileInfo] = None


class UploadResponse(BaseModel):
    files: list[FileUploadResponse]
    total_files: int
    total_size: int

    @classmethod
    def from_dict(cls, obj: dict) -> "Optional[UploadResponse]":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return UploadResponse.model_validate(obj)

        return UploadResponse(**obj)


class ToolConfigOpenAPI(ToolConfigBase):
    type: Literal[ToolType.OPENAPI] = ToolType.OPENAPI.value
    openapi_schema: dict
    authentication: Optional[AuthenticationConfig] = Field(default=None)


class ToolConfigKnowledge(ToolConfigBase):
    type: Literal[ToolType.KNOWLEDGE] = ToolType.KNOWLEDGE.value
    knowledge_id: UUID4
    knowledge_metadata: KnowledgeMetadata
    embedding_model: EmbeddingModel


class ToolConfigMCP(ToolConfigBase):
    type: Literal[ToolType.MCP.value] = ToolType.MCP.value

    mcp_id: UUID4
    tool_name: str
    tool_schema: MCPToolSchema
    url: str
    headers: dict[str, str] | None = None
    params: dict[str, str] | None = None


ToolConfig = Annotated[
    ToolConfigPGVector
    | ToolConfigPineconeVectorDB
    | ToolConfigSQLDatabasePostgres
    | ToolConfigSQLDatabaseMySQL
    | ToolConfigSQLDatabaseMSSQL
    | ToolConfigSQLDatabaseOracle
    | ToolConfigBigQuery
    | ToolConfigOpenAPI
    | ToolConfigKnowledge
    | ToolConfigMCP,
    Discriminator("type"),
]

SQL_TOOLS = Annotated[
    ToolConfigSQLDatabasePostgres
    | ToolConfigSQLDatabaseMySQL
    | ToolConfigSQLDatabaseMSSQL
    | ToolConfigSQLDatabaseOracle
    | ToolConfigBigQuery,
    Discriminator("type"),
]

ContextConfig = Annotated[
    ToolConfigKnowledge
    | ToolConfigPGVector
    | ToolConfigPineconeVectorDB
    | ToolConfigSQLDatabasePostgres
    | ToolConfigSQLDatabaseMySQL
    | ToolConfigSQLDatabaseMSSQL
    | ToolConfigSQLDatabaseOracle
    | ToolConfigBigQuery
    | ToolConfigPGVector
    | ToolConfigPineconeVectorDB,
    Discriminator("type"),
]


class ToolDef(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str
    config: ToolConfig


class TableMetadata(BaseModel):
    table_name: str
