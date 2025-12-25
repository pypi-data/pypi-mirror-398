# Changelog

All notable changes to the SPT Neo RAG Python Client SDK will be documented in this file.

## [0.3.0] - 2025-01-27

### Added

#### Missing Endpoints Added (Completeness Update)
**Query Endpoints (`client.queries`):**
- **`retrieve_sources(payload)`**: Retrieve relevant sources without generating an answer (for OpenWebUI integration)
- **`retrieve_sources_sync(payload)`**: Synchronous version

**Task Endpoints (`client.tasks`):**
- **`get_knowledge_base_tasks(kb_id)`**: Get all tasks related to a knowledge base
- **`get_knowledge_base_tasks_sync(kb_id)`**: Synchronous version

**New Models:**
- `SourcesResponse`: Response model for sources-only retrieval

#### New RAPTOR Endpoints Module (`client.raptor`)
RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) support for hierarchical document indexing:
- **`create_tree(knowledge_base_id, ...)`**: Create a new RAPTOR tree for a knowledge base
- **`get_tree(tree_id)`**: Get RAPTOR tree by ID
- **`list_trees_for_kb(kb_id, active_only=True)`**: List all RAPTOR trees for a knowledge base
- **`update_tree(tree_id, tree_update)`**: Update RAPTOR tree configuration
- **`delete_tree(tree_id)`**: Delete a RAPTOR tree
- **`rebuild_tree(tree_id, config=None)`**: Rebuild an existing RAPTOR tree
- **`get_tree_nodes(tree_id, level=None)`**: Get nodes from a RAPTOR tree
- **`get_tree_statistics(tree_id)`**: Get statistics about a RAPTOR tree
- **`get_system_stats()`**: Get system-wide RAPTOR statistics
- **`get_kb_stats(kb_id)`**: Get RAPTOR stats for a knowledge base
- **`build_tree_for_kb(kb_id, config=None)`**: Build RAPTOR tree for a knowledge base
- **`get_tree_status(kb_id)`**: Get tree status for a knowledge base

#### New Dashboard Endpoints Module (`client.dashboard`)
Admin-only dashboard metrics and analytics:
- **`get_metrics()`**: Get comprehensive platform metrics (database, graph, documents, chunks)
- **`get_analytics(period="30d")`**: Get time-series analytics with customizable period (7d/30d/90d/1y)
- **`get_documents_by_mime_type(mime_type, period="30d", limit=50)`**: Get documents filtered by MIME type

#### New Settings Endpoints Modules (`client.settings`, `client.system_settings`)
**Public Settings (`client.settings`):**
- **`get_public_settings()`**: Get public-facing settings (no auth required)

**System Settings (`client.system_settings` - Admin only):**
- **`get_settings()`**: Get system settings with masked API keys
- **`update_settings(settings_update)`**: Update system settings with encryption
- **`reset_setting(setting_key)`**: Reset setting to default value
- **`clear_cache()`**: Clear settings cache
- **`create_configuration(scope, key, config, ...)`**: Create configuration entry
- **`list_configurations(...)`**: List configurations with filtering
- **`get_configuration(config_id)`**: Get specific configuration by ID
- **`get_configurations_by_scope(scope, ...)`**: Get configs by scope
- **`get_configuration_by_scope_key(scope, key)`**: Get config by scope and key
- **`update_configuration(config_id, ...)`**: Update configuration
- **`delete_configuration(config_id)`**: Delete configuration

#### New Models
**RAPTOR Models:**
- `RaptorTreeStatus` enum: PENDING, BUILDING, COMPLETED, FAILED, UPDATING
- `RaptorNodeType` enum: LEAF, CLUSTER, SUMMARY
- `RaptorTreeCreate`: Tree creation schema
- `RaptorTreeUpdate`: Tree update schema
- `RaptorTreeResponse`: Tree response with metadata
- `RaptorNodeResponse`: Node response with embeddings and relationships

**Settings Models:**
- `PublicSettings`: Public-facing settings model

### Updated
- **Version bumped from 0.2.2 to 0.3.0**
- **Client Documentation**: Updated to reflect new endpoint modules
- **Type Hints**: All new endpoints fully typed with Pydantic models

### Technical Improvements
- Comprehensive RAPTOR tree management for hierarchical document retrieval
- Admin dashboard with real-time metrics and analytics
- Flexible system configuration management with encryption support
- Consistent error handling across all new endpoints
- Full async support for all new operations

### Compatibility
- **Backwards Compatible**: All existing functionality remains unchanged
- **API Compatibility**: Compatible with SPT Neo RAG API v1 (latest endpoints)
- **Python Support**: Python 3.9+

### Example Usage

```python
from spt_neo_rag_client import NeoRagClient
from spt_neo_rag_client.models import RaptorTreeCreate

async with NeoRagClient(base_url="https://api.example.com", api_key="your-key") as client:
    # RAPTOR Operations
    kb_id = "your-kb-id"

    # Build RAPTOR tree
    tree = await client.raptor.build_tree_for_kb(
        kb_id=kb_id,
        config={
            "max_depth": 3,
            "cluster_size": 10,
            "summary_length": 200
        }
    )
    print(f"Tree created: {tree.id}, status: {tree.status}")

    # Get tree status
    status = await client.raptor.get_tree_status(kb_id)
    print(f"Tree ready: {status['is_ready']}")

    # Dashboard Metrics (admin only)
    metrics = await client.dashboard.get_metrics()
    print(f"Total documents: {metrics['document_stats']['total_documents']}")

    analytics = await client.dashboard.get_analytics(period="30d")
    print(f"Documents over time: {analytics['documents_over_time']}")

    # Settings
    public_settings = await client.settings.get_public_settings()
    print(f"Registration enabled: {public_settings.enable_user_registration}")

    # System Settings (admin only)
    sys_settings = await client.system_settings.get_settings()

    # Update specific setting
    await client.system_settings.update_settings({
        "OPENAI_API_KEY": "new-key-value"  # Will be encrypted
    })
```

## [0.2.0] - 2025-01-03

### Added

#### New BM25 Endpoints Module (`client.bm25`)
- **`get_bm25_index_status(knowledge_base_id)`**: Get BM25 index status and metadata for a knowledge base
- **`build_bm25_index(knowledge_base_id, k1=1.2, b=0.75)`**: Build or rebuild BM25 index with custom parameters
- **`delete_bm25_index(knowledge_base_id)`**: Delete BM25 index for a knowledge base
- **`check_bm25_availability(knowledge_base_id)`**: Check if BM25 enhancement is available
- All methods include both async and sync versions (`*_sync`)

#### Enhanced Admin Endpoints (`client.admin`)
**Backup Management:**
- **`list_backups()`**: List all available database backups
- **`create_backup()`**: Initiate a database backup
- **`restore_backup(backup_filename)`**: Restore database from a backup
- **`delete_backup(backup_filename)`**: Delete a specific backup file
- **`download_backup(backup_filename)`**: Download a backup file

**System Monitoring:**
- **`get_rate_limit_stats()`**: Get current rate limiting statistics
- **`get_system_metrics()`**: Get comprehensive system metrics
- **`clear_rate_limit_cache()`**: Clear rate limiting cache for debugging

#### Enhanced Models Endpoints (`client.models`)
- **`get_model_names(provider, model_type=None)`**: Get available model names for a provider
- **`get_providers()`**: Get list of available providers

### Updated
- **Version bumped from 0.1.0 to 0.2.0**
- **README.md**: Added comprehensive documentation for BM25 endpoints with examples
- **Client Documentation**: Updated endpoint list to include BM25 operations

### Technical Improvements
- All new endpoints follow the established pattern of async/sync method pairs
- Comprehensive error handling with `NeoRagApiError` exceptions
- Consistent parameter validation and response handling
- Type hints throughout all new modules

### Compatibility
- **Backwards Compatible**: All existing functionality remains unchanged
- **API Compatibility**: Compatible with SPT Neo RAG API v1
- **Python Support**: Python 3.7+

### Example Usage

```python
# BM25 Operations
kb_id = "your-knowledge-base-id"

# Check availability and build index
availability = await client.bm25.check_bm25_availability(kb_id)
if availability['available']:
    build_result = await client.bm25.build_bm25_index(kb_id, k1=1.2, b=0.75)
    print(f"Build task: {build_result['task_id']}")

# Admin backup operations
backups = await client.admin.list_backups()
backup_task = await client.admin.create_backup()

# Enhanced model queries
providers = await client.models.get_providers()
openai_models = await client.models.get_model_names("openai")
```

## [0.1.0] - 2024-12-XX

### Added
- Initial release of SPT Neo RAG Python Client SDK
- Authentication support (API key and username/password)
- Core endpoint modules:
  - Admin operations
  - API key management
  - Content operations
  - Document management
  - Health checks
  - Knowledge base management
  - Knowledge graph operations
  - Query execution
  - Structured schema management
  - Task management
  - Team management
  - User management
  - Webhook configuration
- Async and sync method support for all operations
- Comprehensive error handling and exception classes
- Type hints and Pydantic model integration 