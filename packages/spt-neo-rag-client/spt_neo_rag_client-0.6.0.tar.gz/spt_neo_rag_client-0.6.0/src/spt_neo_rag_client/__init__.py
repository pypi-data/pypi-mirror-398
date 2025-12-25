"""
SPT Neo RAG Client.

A Python client library for interacting with the SPT Neo RAG API.
"""

__version__ = "0.5.0"

from .client import NeoRagClient
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    NeoRagApiError,
    NeoRagException,
    NetworkError,
)
from .models import (
    # Enums
    AllowedWebhookMethods,
    # API Key models
    ApiKeyCreate,
    ApiKeyFullResponse,
    ApiKeyResponse,
    ApiKeyUpdate,
    AuditCheckResponse,
    AuditCleanupResponse,
    AuditRecordResponse,
    BoundingBox,
    # Utility models
    CountResponse,
    DetailedHealthCheckResponse,
    DocumentChunkResponse,
    DocumentContentResponse,
    # Document models
    DocumentCreate,
    DocumentPageImageResponse,
    DocumentResponse,
    DocumentUpdate,
    # Health models
    HealthCheckComponent,
    HealthCheckResponse,
    # Knowledge Graph models
    KGEntityResponse,
    KGPathSegment,
    KGProcessedDocumentResponse,
    KGRelationshipDetailResponse,
    KGRelationshipInfo,
    KGRelationshipNode,
    KnowledgeGraphCreate,
    KnowledgeGraphUpdate,
    KnowledgeGraphResponse,
    KnowledgeBaseConfigUpdate,
    # Knowledge Base models
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseResponseMinimal,
    KnowledgeBaseUpdate,
    KnowledgeBaseWebhookConfigUpdate,
    KnowledgeGraphExtractionStrategy,
    LicenseStatusResponse,
    MaintenanceResponse,
    ModelCreateRequest,
    ModelDeleteResponse,
    # Model management
    ModelInfo,
    ModelUpdateRequest,
    PaginatedKGEntityResponse,
    PasswordResetRequest,
    PublicSettings,
    # Query models
    AgenticConfig,
    QueryRequest,
    QueryResponse,
    QueryResult,
    QueryResultSource,
    QueryStrategyResponse,
    RaptorNodeResponse,
    RaptorNodeType,
    # RAPTOR models
    RaptorTreeCreate,
    RaptorTreeResponse,
    RaptorTreeStatus,
    RaptorTreeUpdate,
    SourcesResponse,
    StringListResponse,
    # Structured Schema models
    StructuredSchemaCreateRequest,
    StructuredSchemaResponse,
    StructuredSchemaUpdateRequest,
    # Task models
    TaskResponse,
    # Team models
    TeamCreate,
    TeamDetailResponse,
    TeamResponse,
    TeamUpdate,
    # User models
    Token,
    # Admin models
    TokenUsageRecord,
    TokenUsageResponse,
    UserCreate,
    UserResponse,
    UserResponseMinimal,
    UserUpdate,
)

__all__ = [
    # Client
    "NeoRagClient",
    # Exceptions
    "NeoRagException",
    "NeoRagApiError",
    "AuthenticationError",
    "ConfigurationError",
    "NetworkError",
    # Enums
    "AllowedWebhookMethods",
    "KnowledgeGraphExtractionStrategy",
    "RaptorTreeStatus",
    "RaptorNodeType",
    # User models
    "Token",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "UserResponseMinimal",
    "PasswordResetRequest",
    # API Key models
    "ApiKeyCreate",
    "ApiKeyResponse",
    "ApiKeyFullResponse",
    "ApiKeyUpdate",
    # Knowledge Base models
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseConfigUpdate",
    "KnowledgeBaseResponse",
    "KnowledgeBaseResponseMinimal",
    "KnowledgeBaseWebhookConfigUpdate",
    # Document models
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentChunkResponse",
    "DocumentPageImageResponse",
    "DocumentContentResponse",
    "BoundingBox",
    # Query models
    "AgenticConfig",
    "QueryRequest",
    "QueryResponse",
    "QueryResult",
    "QueryResultSource",
    "QueryStrategyResponse",
    "SourcesResponse",
    # Task models
    "TaskResponse",
    # Structured Schema models
    "StructuredSchemaCreateRequest",
    "StructuredSchemaUpdateRequest",
    "StructuredSchemaResponse",
    # Team models
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamDetailResponse",
    # Health models
    "HealthCheckComponent",
    "HealthCheckResponse",
    "DetailedHealthCheckResponse",
    # Knowledge Graph models
    "KGEntityResponse",
    "KGRelationshipNode",
    "KGRelationshipInfo",
    "KGRelationshipDetailResponse",
    "KGPathSegment",
    "KGProcessedDocumentResponse",
    "PaginatedKGEntityResponse",
    "KnowledgeGraphCreate",
    "KnowledgeGraphUpdate",
    "KnowledgeGraphResponse",
    # Model management
    "ModelInfo",
    "ModelCreateRequest",
    "ModelUpdateRequest",
    "ModelDeleteResponse",
    # RAPTOR models
    "RaptorTreeCreate",
    "RaptorTreeUpdate",
    "RaptorTreeResponse",
    "RaptorNodeResponse",
    # Admin models
    "TokenUsageRecord",
    "TokenUsageResponse",
    "MaintenanceResponse",
    "AuditRecordResponse",
    "AuditCheckResponse",
    "AuditCleanupResponse",
    "LicenseStatusResponse",
    # Utility models
    "CountResponse",
    "StringListResponse",
    "PublicSettings",
]
