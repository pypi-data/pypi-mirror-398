"""
Models for the SPT Neo RAG Client.

These Pydantic models mirror the API's data models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AllowedWebhookMethods(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"

class KnowledgeGraphExtractionStrategy(str, Enum):
    LLM = "llm"
    SPACY = "spacy"
    CUSTOM = "custom"

class Token(BaseModel):
    """Authentication token response model."""
    access_token: str
    token_type: str
    expires_at: datetime
    user_id: str


class UserCreate(BaseModel):
    """User creation model."""
    email: str
    password: str
    name: str


class UserResponse(BaseModel):
    """User response model."""
    id: UUID
    email: str
    name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    """User update model."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    # Note: is_superuser is typically handled server-side, not updated by user/client
    # is_superuser: Optional[bool] = None


class UserResponseMinimal(BaseModel):
    """Minimal user response for team context."""
    id: UUID
    name: str
    email: EmailStr


class ApiKeyCreate(BaseModel):
    """API key creation model."""
    name: str
    scopes: str = "query"
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    """API key response model."""
    id: UUID
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    

class ApiKeyFullResponse(ApiKeyResponse):
    """API key response with full key (only returned at creation)."""
    api_key: str


class ApiKeyUpdate(BaseModel):
    """API key update model."""
    name: Optional[str] = None
    scopes: Optional[str] = None
    is_active: Optional[bool] = None
    expires_in_days: Optional[int] = None


class KnowledgeBaseCreate(BaseModel):
    """Knowledge base creation model."""
    name: str
    description: Optional[str] = None

    # Embedding configuration
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-large"

    # Chunking strategy configuration
    chunking_strategy: str = "recursive"
    chunking_config: Optional[Dict[str, Any]] = None

    # Query strategy configuration
    query_strategy: str = "hybrid"
    query_config: Optional[Dict[str, Any]] = None

    # Access control
    credentials: List[str] = Field(default_factory=lambda: ["ALL"])
    is_active: bool = True

    # Webhook configuration
    webhook_url: Optional[str] = None
    is_webhook_enabled: bool = False
    webhook_method: AllowedWebhookMethods = AllowedWebhookMethods.POST
    webhook_secret: Optional[str] = None

    # Knowledge Graph configuration
    enable_knowledge_graph: bool = False
    kg_extraction_strategy: KnowledgeGraphExtractionStrategy = KnowledgeGraphExtractionStrategy.LLM
    kg_confidence_threshold: float = 0.7
    kg_auto_extract: bool = True

    # RAPTOR configuration
    enable_raptor: Optional[bool] = None
    raptor_max_depth: Optional[int] = None
    raptor_cluster_size: Optional[int] = None
    raptor_summary_length: Optional[int] = None

    # BM25 configuration
    auto_build_bm25: Optional[bool] = None
    bm25_k1: Optional[float] = None
    bm25_b: Optional[float] = None


class KnowledgeBaseUpdate(BaseModel):
    """Knowledge base update model."""
    name: Optional[str] = None
    description: Optional[str] = None

    # Embedding configuration
    embedding_model: Optional[str] = None
    embedding_provider: Optional[str] = None

    # Chunking strategy configuration
    chunking_strategy: Optional[str] = None
    chunking_config: Optional[Dict[str, Any]] = None

    # Query strategy configuration
    query_strategy: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None

    # Access control
    credentials: Optional[List[str]] = None
    is_active: Optional[bool] = None

    # Webhook configuration
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_webhook_enabled: Optional[bool] = None
    webhook_method: Optional[AllowedWebhookMethods] = None

    # Knowledge Graph configuration
    enable_knowledge_graph: Optional[bool] = None
    kg_extraction_strategy: Optional[str] = None
    kg_confidence_threshold: Optional[float] = None

    # RAPTOR configuration
    enable_raptor: Optional[bool] = None
    raptor_max_depth: Optional[int] = None
    raptor_cluster_size: Optional[int] = None
    raptor_summary_length: Optional[int] = None

    # BM25 configuration
    auto_build_bm25: Optional[bool] = None
    bm25_k1: Optional[float] = None
    bm25_b: Optional[float] = None


class KnowledgeBaseConfigUpdate(BaseModel):
    """Knowledge base configuration update model."""
    embedding_model: Optional[str] = None
    embedding_provider: Optional[str] = None
    chunking_strategy: Optional[str] = None
    chunking_config: Optional[Dict[str, Any]] = None
    query_strategy: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None


class KnowledgeBaseResponse(BaseModel):
    """Knowledge base response model."""
    id: UUID
    name: str
    description: Optional[str] = None

    # Embedding configuration
    embedding_model: str
    embedding_provider: str
    embedding_dimension: int

    # Configuration versioning
    config_version: int
    last_config_update: datetime

    # Chunking strategy configuration
    chunking_strategy: str
    chunking_config: Optional[Dict[str, Any]] = None

    # Query strategy configuration
    query_strategy: str
    query_config: Optional[Dict[str, Any]] = None

    # Document count
    documents_count: Optional[int] = 0

    # Access control
    credentials: List[str]
    is_active: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Webhook configuration
    webhook_url: Optional[str] = None
    is_webhook_enabled: bool = False
    webhook_method: AllowedWebhookMethods = AllowedWebhookMethods.POST
    webhook_secret_is_set: bool = False

    # Knowledge Graph configuration
    enable_knowledge_graph: bool = False
    kg_extraction_strategy: str = "llm"
    kg_confidence_threshold: float = 0.7
    kg_entity_count: Optional[int] = 0
    kg_relationship_count: Optional[int] = 0

    # RAPTOR configuration
    enable_raptor: bool = False
    raptor_max_depth: int = 3
    raptor_cluster_size: int = 10
    raptor_summary_length: int = 200
    raptor_tree_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseResponseMinimal(BaseModel):
    """Minimal KB response for team context."""
    id: UUID
    name: str


class DocumentCreate(BaseModel):
    """Document creation model (used internally)."""
    name: str
    knowledge_base_id: UUID
    description: Optional[str] = None
    source: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    processor_type: str = "langchain"
    processor_config: Optional[Dict[str, Any]] = None
    credentials: Optional[List[str]] = None
    structured_content_type: Optional[str] = None
    structured_content: Optional[bool] = False


class DocumentUpdate(BaseModel):
    """Document update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    credentials: Optional[List[str]] = None
    structured_content_type: Optional[str] = None
    structured_content: Optional[bool] = False


class BoundingBox(BaseModel):
    """Bounding box model for text location on page."""
    left: float
    top: float
    right: float
    bottom: float
    coord_origin: str = "BOTTOMLEFT"


class DocumentPageImageResponse(BaseModel):
    """Document page image response model."""
    id: UUID
    page_number: int
    image_path: str
    image_url: Optional[str] = None
    width: float
    height: float


class DocumentChunkResponse(BaseModel):
    """Document chunk response model."""
    id: UUID
    document_id: UUID
    content: str
    chunk_index: Optional[int] = None
    page_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    bounding_box: Optional[BoundingBox] = None
    created_at: datetime
    

class DocumentResponse(BaseModel):
    """Document response model."""
    id: UUID
    knowledge_base_id: UUID
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    mime_type: str
    original_path: str
    processed_path: Optional[str] = None
    content_path: Optional[str] = None
    status: str
    doc_metadata: Optional[Dict[str, Any]] = None
    processor_type: str
    processor_config: Optional[Dict[str, Any]] = None
    chunk_count: Optional[int] = None
    page_count: Optional[int] = None
    processed_at: Optional[datetime] = None
    is_active: bool
    error_message: Optional[str] = None
    content_checksum: Optional[str] = None
    credentials: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    structured_content: Optional[bool] = False
    structured_content_type: Optional[str] = None
    structured_content_path: Optional[str] = None
    structured_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class QueryResultSource(BaseModel):
    """Source in query result."""
    document_id: UUID
    document_url: Optional[str] = None
    chunk_id: UUID
    knowledge_base_id: UUID  # Required field
    document_name: str
    content: str
    page_number: Optional[int] = None
    image_url: Optional[str] = None
    relevance_score: float
    metadata: Optional[Dict[str, Any]] = None

    # Document metadata fields - always included when available
    document_description: Optional[str] = None
    document_source: Optional[str] = None
    document_mime_type: Optional[str] = None
    document_page_count: Optional[int] = None
    document_chunk_count: Optional[int] = None
    document_created_at: Optional[datetime] = None
    document_processed_at: Optional[datetime] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    structured_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class QueryResult(BaseModel):
    """Query result model."""
    query: str
    answer: str
    sources: Optional[List[QueryResultSource]] = Field(default_factory=list)
    rewritten_query: Optional[str] = None
    rewritten_queries: Optional[List[str]] = None
    rewrite_strategy_used: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AgenticConfig(BaseModel):
    """Configuration options for the agentic query strategy."""

    max_iterations: int = Field(default=4, ge=1, le=12)
    max_web_search_attempts: int = Field(default=2, ge=0, le=5)
    allow_web_search: bool = False
    web_search_top_k: int = Field(default=3, ge=1, le=10)
    allow_direct_answer_without_retrieval: bool = False
    fallback_strategy: Optional[str] = None
    allowed_tools: Optional[List[str]] = None


class QueryRequest(BaseModel):
    """Query request payload matching server schema."""

    knowledge_base_id: Optional[UUID] = None
    knowledge_base_ids: Optional[List[UUID]] = None
    documents_ids: Optional[List[UUID]] = None
    query: str
    top_k: int = 4
    similarity_threshold: float = 0.7
    use_hybrid_search: bool = True
    include_sources: bool = True
    include_metadata: bool = False
    query_strategy: str = "hybrid"
    retrieval_mode: Optional[str] = None
    search_depth: Optional[int] = None
    query_config: Optional[Dict[str, Any]] = None
    stream: bool = False
    model: Optional[str] = None
    provider: Optional[str] = None
    credentials: List[str] = Field(default_factory=lambda: ["ALL"])
    max_documents: int = 3
    enable_bm25: bool = True
    bm25_weight: float = 0.3
    bm25_combine_method: str = "rrf"
    agentic_config: Optional[AgenticConfig] = None

    # Query Rewriting Parameters
    enable_query_rewriting: bool = False
    rewrite_strategy: Optional[str] = "multi_query"
    rewrite_config: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Query response model."""

    result: QueryResult
    knowledge_base_id: UUID
    knowledge_base_ids: Optional[List[UUID]] = None
    processing_time_ms: float
    token_usage: Optional[Dict[str, int]] = None

    model_config = ConfigDict(populate_by_name=True)


class SourcesResponse(BaseModel):
    """Sources-only response (without answer generation)."""
    query: str
    sources: List[QueryResultSource]
    knowledge_base_id: UUID
    knowledge_base_ids: Optional[List[UUID]] = None
    processing_time_ms: float
    rewritten_query: Optional[str] = None
    rewritten_queries: Optional[List[str]] = None
    rewrite_strategy_used: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class TaskStatus(str, Enum):
    """Enum for task status."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskResponse(BaseModel):
    """Task response model."""
    id: str  # Task ID is a string, not UUID
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    progress: Optional[int] = None

    # Additional metadata
    task_name: str
    task_type: str
    queue: Optional[str] = None
    worker: Optional[str] = None
    eta: Optional[datetime] = None
    priority: Optional[int] = None
    retries: Optional[int] = None
    runtime: Optional[float] = None

    # Related resources
    document_id: Optional[UUID] = None
    knowledge_base_id: Optional[UUID] = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentContentResponse(BaseModel):
    """Response for raw document content (can be large)."""
    content: bytes # Or str, depending on how server streams it


class CountResponse(BaseModel):
    """Generic response for count endpoints."""
    count: int


class StringListResponse(BaseModel):
    """Generic response for endpoints returning a list of strings."""
    items: List[str]


# --- Structured Schema Models ---

class StructuredSchemaCreateRequest(BaseModel):
    """Request to create a structured schema."""
    name: str
    description: Optional[str] = None
    schema_definition: Dict[str, Any]


class StructuredSchemaUpdateRequest(BaseModel):
    """Request to update a structured schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    schema_definition: Optional[Dict[str, Any]] = None


class StructuredSchemaResponse(BaseModel):
    """Response for a structured schema."""
    id: UUID
    name: str
    description: Optional[str] = None
    schema_definition: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Admin Models ---

class TokenUsageRecord(BaseModel):
    """Record for token usage."""
    period_start: datetime
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float


class TokenUsageResponse(BaseModel):
    """Response model for token usage."""
    status: str
    period: str
    usage_data: List[TokenUsageRecord]
    summary: Dict[str, Any]


class MaintenanceResponse(BaseModel):
    """Generic response for maintenance tasks."""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AuditRecordResponse(BaseModel):
    """Response for audit records."""
    id: str
    entity_type: str
    entity_id: str
    status: str
    created_at: datetime
    details: Optional[Dict[str, Any]] = None


class AuditCheckResponse(BaseModel):
    """Response for checking deletion audit."""
    status: str
    message: str
    audit_record: Optional[AuditRecordResponse] = None


class AuditCleanupResponse(BaseModel):
    """Response for cleaning up audited resources."""
    status: str
    message: str
    resources_cleaned: List[str]
    errors: List[str]


class LicenseStatusResponse(BaseModel):
    """License status response model."""
    valid: bool
    customer_name: str = ""
    license_type: str = ""
    days_remaining: int = 0
    expires_at: str = ""
    features: Dict[str, Any] = {}
    error: Optional[str] = None


# --- Team Models ---

class TeamCreate(BaseModel):
    """Team creation model."""
    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    """Team update model."""
    name: Optional[str] = None
    description: Optional[str] = None


class TeamResponse(BaseModel):
    """Team response model."""
    id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID

    model_config = ConfigDict(from_attributes=True)


class TeamDetailResponse(TeamResponse):
    """Detailed team response including members and KBs."""
    users: List[UserResponseMinimal]
    knowledge_bases: List[KnowledgeBaseResponseMinimal]


# --- Health Models ---

class HealthCheckComponent(BaseModel):
    """Component status for detailed health check."""
    status: str
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Simple health check response."""
    status: str
    api_version: str
    service: str


class DetailedHealthCheckResponse(HealthCheckResponse):
    """Detailed health check response."""
    components: Dict[str, HealthCheckComponent]
    checks: List[Dict[str, str]]
    execution_time_ms: float


# --- Query Strategy Models ---

class QueryStrategyResponse(BaseModel):
    """Response for query strategies."""
    strategies: List[str]


# --- Password Reset Model ---

class PasswordResetRequest(BaseModel):
    email: EmailStr


class GenericStatusResponse(BaseModel):
    """Generic response indicating success/failure message."""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Knowledge Graph Models
class KnowledgeGraphCreate(BaseModel):
    """Model for creating knowledge graph metadata."""
    knowledge_base_id: UUID
    extraction_strategy: str = "llm"
    confidence_threshold: float = 0.7
    # LLM-specific configuration (only used when extraction_strategy is "llm")
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM provider for KG extraction (llm strategy only)"
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="LLM model for KG extraction (llm strategy only)"
    )
    kg_schema: Dict[str, Any] = Field(default={}, alias="schema")


class KnowledgeGraphUpdate(BaseModel):
    """Model for updating knowledge graph metadata."""
    extraction_strategy: Optional[str] = None
    confidence_threshold: Optional[float] = None
    # LLM-specific configuration (only used when extraction_strategy is "llm")
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM provider for KG extraction (llm strategy only)"
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="LLM model for KG extraction (llm strategy only)"
    )
    kg_schema: Optional[Dict[str, Any]] = Field(default=None, alias="schema")


class KnowledgeGraphResponse(BaseModel):
    """Knowledge graph metadata response model."""
    id: UUID
    knowledge_base_id: UUID
    entity_count: int = 0
    relationship_count: int = 0
    entity_types: List[str] = []
    relationship_types: List[str] = []
    extraction_strategy: str = "llm"
    confidence_threshold: float = 0.7
    # LLM-specific configuration (only used when extraction_strategy is "llm")
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    kg_schema: Dict[str, Any] = Field(default={}, alias="schema")
    created_at: datetime
    last_updated: datetime


class KGProcessedDocumentResponse(BaseModel):
    """Response for document processing for knowledge graph."""
    entities_extracted: int
    relationships_extracted: int
    status: str
    message: Optional[str] = None


class KGEntityResponse(BaseModel):
    """Knowledge graph entity response model."""
    id: str
    name: str
    entity_type: str
    properties: Dict[str, Any]


class KGRelationshipNode(BaseModel):
    """Knowledge graph relationship node model."""
    id: str
    type: str
    name: Optional[str] = None


class KGRelationshipInfo(BaseModel):
    """Knowledge graph relationship info model."""
    type: str
    properties: Optional[Dict[str, Any]] = None


class KGRelationshipDetailResponse(BaseModel):
    """Knowledge graph relationship detail response model."""
    source: KGRelationshipNode
    relationship: KGRelationshipInfo
    target: KGRelationshipNode
    is_outgoing_from_queried_entity: bool


class KGPathSegment(BaseModel):
    """Knowledge graph path segment model."""
    type: str  # "node" or "relationship"
    # Node specific
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    # Relationship specific
    relationship_type: Optional[str] = None
    # Common
    properties: Optional[Dict[str, Any]] = None


class PaginatedKGEntityResponse(BaseModel):
    """Paginated knowledge graph entity response model."""
    total: int
    entities: List[KGEntityResponse]


# Webhook Models
class AllowedWebhookMethods(str, Enum):
    """Allowed webhook HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"


class KnowledgeBaseWebhookConfigUpdate(BaseModel):
    """Model for updating knowledge base webhook configuration."""
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_webhook_enabled: Optional[bool] = None
    webhook_method: Optional[AllowedWebhookMethods] = None


# Model Info
class ModelInfo(BaseModel):
    """Model information response."""
    id: Optional[str] = None
    name: str  # This is the actual field name from the API
    provider: str
    type: Optional[str] = None  # Made optional since API doesn't always return it
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None
    has_vision: Optional[bool] = None

    @property
    def model_name(self) -> str:
        """Alias for name for backward compatibility."""
        return self.name


class ModelCreateRequest(BaseModel):
    """Model creation request."""
    name: str
    provider: str
    type: str
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None


class ModelUpdateRequest(BaseModel):
    """Model update request."""
    name: Optional[str] = None
    provider: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None


class ModelDeleteResponse(BaseModel):
    """Model deletion response."""
    status: str
    message: str


# ================= RAPTOR Models =================

class RaptorTreeStatus(str, Enum):
    """Enum for RAPTOR tree building status."""
    PENDING = "pending"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATING = "updating"


class RaptorNodeType(str, Enum):
    """Enum for RAPTOR node types."""
    LEAF = "leaf"
    CLUSTER = "cluster"
    SUMMARY = "summary"


class RaptorTreeCreate(BaseModel):
    """Schema for RAPTOR tree creation."""
    knowledge_base_id: UUID
    max_depth: int = Field(default=3, description="Maximum tree depth")
    cluster_size: int = Field(default=10, description="Target cluster size")
    summary_length: int = Field(default=200, description="Summary length (tokens)")
    clustering_config: Optional[Dict[str, Any]] = None
    summarization_config: Optional[Dict[str, Any]] = None


class RaptorTreeUpdate(BaseModel):
    """Schema for RAPTOR tree updates."""
    max_depth: Optional[int] = None
    cluster_size: Optional[int] = None
    summary_length: Optional[int] = None
    status: Optional[str] = None
    current_depth: Optional[int] = None
    total_nodes: Optional[int] = None
    leaf_nodes: Optional[int] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    clustering_config: Optional[Dict[str, Any]] = None
    summarization_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RaptorTreeResponse(BaseModel):
    """Schema for RAPTOR tree response."""
    id: UUID
    knowledge_base_id: UUID
    max_depth: int
    cluster_size: int
    summary_length: int
    status: str
    current_depth: int
    total_nodes: int
    leaf_nodes: int
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    clustering_config: Optional[Dict[str, Any]] = None
    summarization_config: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RaptorNodeResponse(BaseModel):
    """Schema for RAPTOR node response."""
    id: UUID
    tree_id: UUID
    parent_node_id: Optional[UUID] = None
    level: int
    node_type: str
    content: str
    summary: Optional[str] = None
    cluster_id: Optional[int] = None
    cluster_centroid: Optional[List[float]] = None
    embedding: Optional[List[float]] = None
    node_metadata: Optional[Dict[str, Any]] = None
    chunk_ids: Optional[List[UUID]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================= Settings Models =================

class PublicSettings(BaseModel):
    """Public-facing settings model."""
    enable_user_registration: bool = True
