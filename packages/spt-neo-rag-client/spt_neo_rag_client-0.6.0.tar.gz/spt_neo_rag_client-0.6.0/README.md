# SPT Neo RAG Client

A Python client library for interacting with the SPT Neo RAG API, a modern retrieval-augmented generation system with advanced document processing, semantic search, and knowledge graph capabilities.

This client provides both asynchronous (`async`/`await`) methods and corresponding synchronous wrappers for ease of use in different application contexts.

## Quick Start

```python
from spt_neo_rag_client import NeoRagClient
import asyncio

async def main():
    # Initialize client with API key
    client = NeoRagClient(
        base_url="https://your-api-url.com",
        api_key="your-api-key"
    )

    # List knowledge bases
    kbs = await client.knowledge_bases.list_knowledge_bases(limit=10)
    print(f"Found {len(kbs)} knowledge bases")

    # Close the client
    await client.close()

# Run
asyncio.run(main())
```

Or use synchronous methods:

```python
from spt_neo_rag_client import NeoRagClient

client = NeoRagClient(
    base_url="https://your-api-url.com",
    api_key="your-api-key"
)

# Use sync methods (append _sync to method names)
kbs = client.knowledge_bases.list_knowledge_bases_sync(limit=10)
print(f"Found {len(kbs)} knowledge bases")
```

## Features

- 🔐 **Flexible Authentication**: API key or username/password authentication
- 📚 **Knowledge Base Management**: Create, update, and manage knowledge bases
- 📄 **Document Processing**: Upload and process various document formats (PDF, DOCX, TXT, etc.)
- 🔍 **Advanced Querying**: Multiple query strategies (hybrid search, knowledge graph, RAPTOR, agentic, etc.)
- ✨ **Query Rewriting**: Improve retrieval with HyDE, multi-query, step-back, decomposition, and fusion strategies
- 🤖 **Agentic Queries**: AI agent with iterative reasoning and optional web search
- 🕸️ **Knowledge Graph**: Entity extraction and relationship mapping
- 👥 **Team Collaboration**: Share knowledge bases with teams
- 🔑 **API Key Management**: Generate and manage API keys for service accounts
- ⚡ **Async & Sync Support**: Both async/await and synchronous method variants
- 📊 **Admin Operations**: System statistics, token usage tracking, and license management

## Installation

```bash
# Using pip
pip install spt-neo-rag-client

# Or using uv
uv pip install spt-neo-rag-client

# Or install from source (development)
uv pip install -e /path/to/spt-neo-rag-client
```

## Authentication

The client supports two authentication methods:

1.  **API Key (Recommended for service accounts/scripts):**

    ```python
    from spt_neo_rag_client import NeoRagClient
    
    client = NeoRagClient(
        base_url="https://your-api-base-url.com", 
        api_key="your-spt-api-key"
    )
    # Ready to make authenticated requests
    ```

2.  **Username/Password (Suitable for user-facing applications):**

    ```python
    import asyncio
    from spt_neo_rag_client import NeoRagClient
    
    async def main():
        client = NeoRagClient(base_url="https://your-api-base-url.com")
        try:
            token_info = await client.login(username="user@example.com", password="your_password")
            print(f"Login successful! Token expires at: {token_info.expires_at}")
            # Client is now authenticated for subsequent requests
            
            # Example: Get current user
            user = await client.get_current_user()
            print(f"Authenticated as: {user.name}")
            
            # Remember to close the client when done
            await client.close()
            
        except Exception as e:
            print(f"Authentication failed: {e}")
    
    # Run the async function
    asyncio.run(main())
    ```

    **Synchronous Login:**

    ```python
    from spt_neo_rag_client import NeoRagClient
    
    client = NeoRagClient(base_url="https://your-api-base-url.com")
    try:
        token_info = client.login_sync(username="user@example.com", password="your_password")
        print(f"Login successful! Token expires at: {token_info.expires_at}")
        user = client.get_current_user_sync()
        print(f"Authenticated as: {user.name}")
    except Exception as e:
        print(f"Authentication failed: {e}")
    ```

## Usage

The client provides access to different API endpoint groups via attributes. Each group contains methods for interacting with specific resources.

-   `client.admin`: Admin operations
-   `client.api_keys`: API key management for the current user
-   `client.bm25`: BM25 index operations for enhanced text search
-   `client.content`: Content retrieval from storage
-   `client.dashboard`: Dashboard metrics and analytics (admin)
-   `client.documents`: Document management
-   `client.health`: Health checks
-   `client.knowledge_bases`: Knowledge base management
-   `client.knowledge_graph`: Knowledge graph entity and relationship management
-   `client.models`: Model management and provider listing
-   `client.queries`: Query execution
-   `client.raptor`: RAPTOR tree management for hierarchical retrieval
-   `client.settings`: Public settings access
-   `client.structured_schemas`: Structured schema management
-   `client.system_settings`: System configuration (admin)
-   `client.tasks`: Background task management
-   `client.teams`: Team management
-   `client.users`: User management (most require admin privileges)
-   `client.webhooks`: Webhook configuration for knowledge bases

### Async and Sync Methods

All API interaction methods have both an asynchronous version (e.g., `await client.knowledge_bases.list_knowledge_bases()`) and a synchronous wrapper (e.g., `client.knowledge_bases.list_knowledge_bases_sync()`). Use the version that best fits your application's architecture.

**Note:** The examples below primarily use the `async`/`await` syntax. To use the synchronous version, simply call the corresponding method ending in `_sync`.

### Examples

*(Assume `client` is an initialized and authenticated `NeoRagClient` instance)*

#### Knowledge Bases (`client.knowledge_bases`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseConfigUpdate

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...") 
    await client.login("...") 
    # or client = NeoRagClient(base_url="...", api_key="...")
    return client
# ----------------------------------------------

async def kb_examples():
    client = await get_authenticated_client()
    try:
        # List knowledge bases
        kbs = await client.knowledge_bases.list_knowledge_bases(limit=10)
        print(f"Found {len(kbs)} knowledge bases.")

        # Create a new knowledge base
        new_kb_data = KnowledgeBaseCreate(
            name="My Async KB",
            description="An example knowledge base",
            kb_type="default", # Or other type if available
            credentials=["team-alpha"], # Restrict access
            config={"embedding_model": "text-embedding-ada-002"}
        )
        created_kb = await client.knowledge_bases.create_knowledge_base(new_kb_data)
        print(f"Created KB: {created_kb.id} - {created_kb.name}")
        kb_id = created_kb.id

        # Get KB count
        count_response = await client.knowledge_bases.count_knowledge_bases()
        print(f"Total KBs: {count_response.count}")

        # Get a specific KB
        kb = await client.knowledge_bases.get_knowledge_base(kb_id)
        print(f"Retrieved KB: {kb.name} with {kb.documents_count} documents")

        # Update KB details
        update_data = KnowledgeBaseUpdate(description="Updated description")
        updated_kb = await client.knowledge_bases.update_knowledge_base(kb_id, update_data)
        print(f"Updated KB description: {updated_kb.description}")

        # Update KB config
        config_update = KnowledgeBaseConfigUpdate(config={"chunk_size": 512})
        configured_kb = await client.knowledge_bases.update_knowledge_base_config(kb_id, config_update)
        print(f"Updated KB config: {configured_kb.config}")

        # Get available embedding models
        embedding_models = await client.knowledge_bases.get_embedding_models(provider="openai")
        print(f"\nAvailable embedding models for OpenAI: {embedding_models}")

        # Delete the KB
        delete_status = await client.knowledge_bases.delete_knowledge_base(kb_id)
        print(f"Delete status: {delete_status}")

    finally:
        await client.close()

# Run example
# asyncio.run(kb_examples())
```

#### BM25 Index Operations (`client.bm25`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...") 
    await client.login("...") 
    # or client = NeoRagClient(base_url="...", api_key="...")
    return client
# ----------------------------------------------

# Assume kb_id is a valid UUID from an existing KB with documents
kb_id = "your-knowledge-base-id"

async def bm25_examples():
    client = await get_authenticated_client()
    try:
        # Check if BM25 is available for the knowledge base
        availability = await client.bm25.check_bm25_availability(kb_id)
        print(f"BM25 availability: {availability}")
        
        # Get current BM25 index status
        try:
            status = await client.bm25.get_bm25_index_status(kb_id)
            print(f"BM25 index status: {status['status']}")
            print(f"Document count: {status['document_count']}")
            print(f"Vocabulary size: {status['vocabulary_size']}")
        except Exception as e:
            print(f"No existing BM25 index: {e}")
        
        # Build/rebuild BM25 index with custom parameters
        print("Building BM25 index...")
        build_response = await client.bm25.build_bm25_index(
            kb_id, 
            k1=1.2,  # Term frequency saturation parameter
            b=0.75   # Field length normalization parameter
        )
        print(f"Build task started: {build_response['task_id']}")
        
        # Wait a moment and check status again
        await asyncio.sleep(5)
        status = await client.bm25.get_bm25_index_status(kb_id)
        print(f"Updated status: {status['status']}")
        
        # Delete BM25 index if needed
        # delete_response = await client.bm25.delete_bm25_index(kb_id)
        # print(f"Delete response: {delete_response}")
        
    finally:
        await client.close()

# Run example
# asyncio.run(bm25_examples())
```

#### Documents (`client.documents`)

```python
import asyncio
import io
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, DocumentUpdate

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

# Assume kb_id is a valid UUID from an existing KB
kb_id = UUID("your-knowledge-base-id") 

async def doc_examples():
    client = await get_authenticated_client()
    doc_id = None
    try:
        # Get available processors and chunking strategies
        processors = await client.documents.get_processors()
        strategies = await client.documents.get_chunking_strategies()
        print(f"Available Processors: {processors}")
        print(f"Available Strategies: {strategies}")
        
        # Create a dummy file in memory
        dummy_content = b"This is the content of my test document."
        file_object = io.BytesIO(dummy_content)
        file_name = "test_document.txt"

        # Upload a document
        print(f"Uploading {file_name}...")
        uploaded_doc = await client.documents.upload_document(
            file=file_object,
            file_name=file_name,
            name="My Test Document",
            knowledge_base_id=kb_id,
            description="A simple test document",
            metadata={"category": "testing"},
            credentials=["team-alpha"] # Optional access control
            # Add structured extraction params if needed:
            # extract_structured_content=True,
            # structured_document_type=StructuredDocumentType.GENERIC
        )
        doc_id = uploaded_doc.id
        print(f"Uploaded Document: {doc_id} - Status: {uploaded_doc.status}")

        # List documents in the KB
        docs = await client.documents.list_documents(knowledge_base_id=kb_id)
        print(f"Found {len(docs)} documents in KB {kb_id}.")

        # Get document count
        doc_count = await client.documents.count_documents(knowledge_base_id=kb_id)
        print(f"Total documents in KB: {doc_count}")

        # Get the specific document
        doc = await client.documents.get_document(doc_id)
        print(f"Retrieved Document: {doc.name}, Status: {doc.status}")

        # Get document content (raw bytes)
        content = await client.documents.get_document_content(doc_id)
        print(f"Retrieved content (first 20 bytes): {content[:20]}...")

        # Update the document
        update_data = DocumentUpdate(description="Updated document description")
        updated_doc = await client.documents.update_document(doc_id, update_data)
        print(f"Updated document description: {updated_doc.description}")

        # Get document chunks (wait briefly for processing if just uploaded)
        await asyncio.sleep(5) # Allow time for initial processing
        chunks = await client.documents.get_document_chunks(doc_id, limit=5)
        print(f"Found {len(chunks)} chunks for document {doc_id}.")

        # Get chunk count
        chunk_count = await client.documents.count_document_chunks(doc_id)
        print(f"Total chunks for document: {chunk_count}")
        
        # Get page images (if applicable, e.g., for PDFs)
        # images = await client.documents.get_document_page_images(doc_id)
        # print(f"Found {len(images)} page images.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up: Delete the document if it was created
        if doc_id:
            try:
                print(f"Deleting document {doc_id}...")
                delete_status = await client.documents.delete_document(doc_id)
                print(f"Document delete status: {delete_status}")
            except Exception as del_e:
                print(f"Error deleting document {doc_id}: {del_e}")
        await client.close()

# Run example
# asyncio.run(doc_examples())
```

#### Queries (`client.queries`)

The client provides three main query methods:
- `retrieve_sources()` - Get relevant sources only (no LLM answer generation)
- `query()` - Full RAG query with LLM-generated answer
- `stream_query()` - Streaming RAG query with real-time token output

```python
import asyncio
from spt_neo_rag_client import NeoRagClient
from spt_neo_rag_client.models import QueryRequest


async def main():
    # Initialize client
    client = NeoRagClient(
        base_url="https://your-api-url.com",
        api_key="your-api-key"
    )

    try:
        # Get a knowledge base to query
        kbs = await client.knowledge_bases.list_knowledge_bases(limit=1)
        if not kbs:
            print("No knowledge bases found.")
            return
        kb_id = kbs[0].id

        query_text = "What is the main topic of the document?"

        # =============================================================
        # Example 1: retrieve_sources - Get sources only (no LLM answer)
        # =============================================================
        print("Example 1: retrieve_sources")
        print("-" * 40)

        sources_response = await client.queries.retrieve_sources(QueryRequest(
            query=query_text,
            knowledge_base_ids=[kb_id],
            top_k=3,
            credentials=["ALL"]
        ))

        print(f"Query: {query_text}")
        print(f"Retrieved {len(sources_response.sources)} sources")
        if sources_response.sources:
            print("Sources:")
            for source in sources_response.sources:
                print(f"  - Doc: {source.document_name}, Score: {source.relevance_score:.2f}")

        # =============================================================
        # Example 2: query - Full RAG query with LLM-generated answer
        # =============================================================
        print("\nExample 2: query (full RAG with LLM answer)")
        print("-" * 40)

        query_response = await client.queries.query(QueryRequest(
            query=query_text,
            knowledge_base_ids=[kb_id],
            top_k=3,
            credentials=["ALL"],
            include_sources=True
        ))

        print(f"Query: {query_text}")
        print(f"Answer: {query_response.result.answer}")
        print(f"Processing time: {query_response.processing_time_ms:.0f}ms")
        if query_response.result.sources:
            print(f"Sources ({len(query_response.result.sources)}):")
            for source in query_response.result.sources:
                print(f"  - Doc: {source.document_name}, Score: {source.relevance_score:.2f}")

        # =============================================================
        # Example 3: stream_query - Streaming RAG query
        # =============================================================
        print("\nExample 3: stream_query (streaming response)")
        print("-" * 40)

        print(f"Query: {query_text}")
        print("Streaming answer: ", end="", flush=True)

        sources = []
        async for chunk in client.queries.stream_query(QueryRequest(
            query=query_text,
            knowledge_base_ids=[kb_id],
            top_k=3,
            credentials=["ALL"],
            include_sources=True
        )):
            # Stream format: {"chunk": "text", "done": false/true, ...}
            # When done=True, sources are included in the chunk
            token = chunk.get("chunk", "")
            if token:
                print(token, end="", flush=True)

            if chunk.get("done"):
                sources = chunk.get("sources", [])

        # Print sources after streaming completes
        if sources:
            print(f"\n\nSources ({len(sources)}):")
            for src in sources:
                print(f"  - Doc: {src.get('document_name')}, Score: {src.get('relevance_score', 0):.2f}")

        # =============================================================
        # Get available query strategies
        # =============================================================
        strategies_response = await client.queries.get_query_strategies()
        print(f"\nAvailable query strategies: {strategies_response.strategies}")

    finally:
        await client.close()


# Run
asyncio.run(main())
```

#### Query Rewriting

Query rewriting improves retrieval quality by transforming the user's query before searching. Available strategies:

- `multi_query` - Generate multiple query variations
- `hyde` - Hypothetical Document Embeddings (generate a hypothetical answer, then search)
- `step_back` - Create a more abstract/general question
- `decomposition` - Break complex queries into sub-queries
- `fusion` - Multi-query with Reciprocal Rank Fusion
- `refinement` - Simple query refinement/clarification

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, QueryRequest

kb_id = UUID("your-knowledge-base-id")

async def query_rewriting_examples():
    client = NeoRagClient(base_url="...", api_key="...")
    try:
        # Query with HyDE (Hypothetical Document Embeddings)
        response = await client.queries.query(QueryRequest(
            query="How does photosynthesis work?",
            knowledge_base_ids=[kb_id],
            enable_query_rewriting=True,
            rewrite_strategy="hyde"
        ))
        print(f"Answer: {response.result.answer}")
        print(f"Strategy used: {response.result.rewrite_strategy_used}")
        print(f"Rewritten query: {response.result.rewritten_query}")

        # Query with multi-query expansion
        response = await client.queries.query(QueryRequest(
            query="What are the benefits of exercise?",
            knowledge_base_ids=[kb_id],
            enable_query_rewriting=True,
            rewrite_strategy="multi_query",
            rewrite_config={"num_queries": 4}  # Generate 4 query variations
        ))
        print(f"Rewritten queries: {response.result.rewritten_queries}")

        # Query with decomposition for complex questions
        response = await client.queries.query(QueryRequest(
            query="Compare the economic impacts of renewable vs fossil fuels and their environmental effects",
            knowledge_base_ids=[kb_id],
            enable_query_rewriting=True,
            rewrite_strategy="decomposition"
        ))
        print(f"Sub-queries: {response.result.rewritten_queries}")

        # Retrieve sources with query rewriting (no answer generation)
        sources = await client.queries.retrieve_sources(QueryRequest(
            query="machine learning applications",
            knowledge_base_ids=[kb_id],
            enable_query_rewriting=True,
            rewrite_strategy="fusion"
        ))
        print(f"Strategy used: {sources.rewrite_strategy_used}")
        print(f"Found {len(sources.sources)} sources")

    finally:
        await client.close()

# asyncio.run(query_rewriting_examples())
```

#### Agentic Queries

The agentic query strategy uses an AI agent that can reason, retrieve documents iteratively, and optionally search the web.

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, QueryRequest, AgenticConfig

kb_id = UUID("your-knowledge-base-id")

async def agentic_query_examples():
    client = NeoRagClient(base_url="...", api_key="...")
    try:
        # Basic agentic query
        response = await client.queries.query(QueryRequest(
            query="What are the key findings from the Q3 report and how do they compare to Q2?",
            knowledge_base_ids=[kb_id],
            query_strategy="agentic",
            agentic_config=AgenticConfig(
                max_iterations=4  # Maximum reasoning steps
            )
        ))
        print(f"Answer: {response.result.answer}")

        # Agentic query with web search fallback
        response = await client.queries.query(QueryRequest(
            query="What are the latest developments in quantum computing?",
            knowledge_base_ids=[kb_id],
            query_strategy="agentic",
            agentic_config=AgenticConfig(
                max_iterations=6,
                allow_web_search=True,  # Enable web search when local knowledge insufficient
                max_web_search_attempts=2,
                web_search_top_k=3,
                fallback_strategy="hybrid"  # Fall back to hybrid if agent fails
            )
        ))
        print(f"Answer: {response.result.answer}")

        # Agentic query allowing direct answers without retrieval
        response = await client.queries.query(QueryRequest(
            query="What is 2 + 2?",
            knowledge_base_ids=[kb_id],
            query_strategy="agentic",
            agentic_config=AgenticConfig(
                allow_direct_answer_without_retrieval=True
            )
        ))
        print(f"Answer: {response.result.answer}")

    finally:
        await client.close()

# asyncio.run(agentic_query_examples())
```

#### API Keys (`client.api_keys`)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient, ApiKeyCreate, ApiKeyUpdate

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

async def api_key_examples():
    client = await get_authenticated_client()
    new_key_id = None
    try:
        # Create a new API key
        create_data = ApiKeyCreate(
            name="My Script Key", 
            scopes="query,read", # Scopes control permissions
            expires_in_days=90
        )
        key_response = await client.api_keys.create_api_key(create_data)
        new_key_id = key_response.id
        print(f"Created API Key: {key_response.name} (ID: {new_key_id})")
        print(f"!!! IMPORTANT: Save the key value now: {key_response.api_key} !!!")

        # List API keys
        keys = await client.api_keys.list_api_keys()
        print(f"\nFound {len(keys)} API keys for this user.")
        for key in keys:
            print(f"  - ID: {key.id}, Name: {key.name}, Active: {key.is_active}")

        # Get the created key
        retrieved_key = await client.api_keys.get_api_key(new_key_id)
        print(f"\nRetrieved Key: {retrieved_key.name}, Expires: {retrieved_key.expires_at}")

        # Update the key (e.g., deactivate it)
        update_data = ApiKeyUpdate(is_active=False)
        updated_key = await client.api_keys.update_api_key(new_key_id, update_data)
        print(f"\nUpdated Key: {updated_key.name}, Active: {updated_key.is_active}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up: Delete the created key
        if new_key_id:
            try:
                print(f"\nDeleting API key {new_key_id}...")
                delete_status = await client.api_keys.delete_api_key(new_key_id)
                print(f"API key delete status: {delete_status}")
            except Exception as del_e:
                print(f"Error deleting API key {new_key_id}: {del_e}")
        await client.close()

# Run example
# asyncio.run(api_key_examples())
```

#### Tasks (`client.tasks`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

# Assume doc_id is a valid UUID from an existing document
doc_id = UUID("your-document-id")

async def task_examples():
    client = await get_authenticated_client()
    try:
        # List recent tasks
        tasks = await client.tasks.list_tasks()
        print(f"Found {len(tasks)} recent tasks.")
        if tasks:
             task_id_to_check = tasks[0].id
             print(f"Checking status of task: {task_id_to_check}")
             
             # Get a specific task status
             task_status = await client.tasks.get_task(task_id_to_check)
             print(f"Task {task_status.id} status: {task_status.status}, Progress: {task_status.progress * 100:.1f}%")

             # Try to cancel the task (might fail if already completed)
             try:
                 cancel_status = await client.tasks.delete_task(task_id_to_check)
                 print(f"Task cancellation request status: {cancel_status}")
             except Exception as cancel_e:
                 print(f"Could not cancel task {task_id_to_check}: {cancel_e}")

        # List all tasks
        all_tasks = await client.tasks.list_tasks()
        print(f"Found {len(all_tasks)} total tasks.")

        # Get tasks related to a specific document
        doc_tasks = await client.tasks.get_document_tasks(doc_id)
        print(f"\nFound {len(doc_tasks)} tasks related to document {doc_id}.")
        for task in doc_tasks:
            print(f"  - Task {task.id}: Type={task.task_type}, Status={task.status}")

    finally:
        await client.close()

# Run example
# asyncio.run(task_examples())
```

#### Teams (`client.teams`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, TeamCreate, TeamUpdate

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

# Assume user_id_to_add and kb_id_to_share are valid UUIDs
user_id_to_add = UUID("uuid-of-another-user")
kb_id_to_share = UUID("uuid-of-a-knowledge-base")

async def team_examples():
    client = await get_authenticated_client()
    team_id = None
    try:
        # Create a team
        create_data = TeamCreate(name="Alpha Squad", description="The A Team")
        team = await client.teams.create_team(create_data)
        team_id = team.id
        print(f"Created Team: {team.name} (ID: {team_id})")

        # List teams
        teams = await client.teams.list_teams()
        print(f"\nFound {len(teams)} teams.")

        # Get team details
        detailed_team = await client.teams.get_team(team_id)
        print(f"\nTeam '{detailed_team.name}' details:")
        print(f"  Members ({len(detailed_team.users)}): {', '.join([u.name for u in detailed_team.users])}")
        print(f"  Shared KBs ({len(detailed_team.knowledge_bases)}): {', '.join([kb.name for kb in detailed_team.knowledge_bases])}")

        # Add a user to the team (requires owner permission)
        try:
            updated_team = await client.teams.add_user_to_team(team_id, user_id_to_add)
            print(f"\nUser {user_id_to_add} added to team {team_id}.")
        except Exception as add_e:
            print(f"\nCould not add user {user_id_to_add}: {add_e}")

        # Share a KB with the team (requires owner permission)
        try:
            share_status = await client.teams.share_kb_with_team(team_id, kb_id_to_share)
            print(f"\nKB {kb_id_to_share} shared with team {team_id}: {share_status}")
        except Exception as share_e:
            print(f"\nCould not share KB {kb_id_to_share}: {share_e}")
            
        # List shared KBs
        shared_kbs = await client.teams.list_shared_kbs_for_team(team_id)
        print(f"\nKBs shared with team {team_id}: {[kb.name for kb in shared_kbs]}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up: Delete the team if created
        if team_id:
            try:
                print(f"\nDeleting team {team_id}...")
                delete_status = await client.teams.delete_team(team_id)
                print(f"Team delete status: {delete_status}")
            except Exception as del_e:
                print(f"Error deleting team {team_id}: {del_e}")
        await client.close()

# Run example
# asyncio.run(team_examples())
```

#### Structured Schemas (`client.structured_schemas`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, StructuredSchemaCreateRequest, StructuredSchemaUpdateRequest

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

async def schema_examples():
    client = await get_authenticated_client()
    schema_id = None
    try:
        # Create a schema
        schema_def = {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string"},
                "total_amount": {"type": "number"},
                "due_date": {"type": "string", "format": "date"}
            },
            "required": ["invoice_id", "total_amount"]
        }
        create_req = StructuredSchemaCreateRequest(
            name="InvoiceSchema",
            description="Schema for invoice documents",
            schema_definition=schema_def
        )
        schema = await client.structured_schemas.create_schema(create_req)
        schema_id = schema.id
        print(f"Created Schema: {schema.name} (ID: {schema_id})")

        # List schemas
        schemas = await client.structured_schemas.list_schemas()
        print(f"\nFound {len(schemas)} schemas.")

        # Get the schema
        retrieved_schema = await client.structured_schemas.get_schema(schema_id)
        print(f"\nRetrieved schema: {retrieved_schema.name}")
        # print(f"Definition: {retrieved_schema.schema_definition}")

        # Update the schema
        update_req = StructuredSchemaUpdateRequest(description="Updated schema for invoices")
        updated_schema = await client.structured_schemas.update_schema(schema_id, update_req)
        print(f"\nUpdated schema description: {updated_schema.description}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up: Delete the schema
        if schema_id:
            try:
                print(f"\nDeleting schema {schema_id}...")
                delete_status = await client.structured_schemas.delete_schema(schema_id)
                print(f"Schema delete status: {delete_status}")
            except Exception as del_e:
                print(f"Error deleting schema {schema_id}: {del_e}")
        await client.close()

# Run example
# asyncio.run(schema_examples())
```

#### Users (`client.users` - Requires Admin)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, UserCreate, UserUpdate

# --- Replace with your actual client setup (MUST be an ADMIN user) ---
async def get_admin_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your ADMIN client here
    client = NeoRagClient(base_url="...")
    await client.login("admin@example.com", "admin_password") 
    return client
# ----------------------------------------------------------------------

async def user_management_examples():
    # WARNING: These operations modify users and require admin privileges.
    client = await get_admin_client()
    new_user_id = None
    try:
        # List users
        users = await client.users.list_users(limit=5, is_active=True)
        print(f"Found {len(users)} active users.")
        for user in users:
             print(f"  - {user.name} ({user.email}), ID: {user.id}")

        # Create a new user
        create_data = UserCreate(
            email="test.user@example.com", 
            password="a-strong-password", 
            name="Test User (Managed)"
        )
        new_user = await client.users.create_user(create_data)
        new_user_id = new_user.id
        print(f"\nCreated User: {new_user.name} (ID: {new_user_id})")

        # Get the new user
        retrieved_user = await client.users.get_user(new_user_id)
        print(f"\nRetrieved User: {retrieved_user.name}, Active: {retrieved_user.is_active}")

        # Update the user (e.g., deactivate)
        update_data = UserUpdate(is_active=False)
        updated_user = await client.users.update_user(new_user_id, update_data)
        print(f"\nUpdated User: {updated_user.name}, Active: {updated_user.is_active}")

        # Update current admin user's details (example - use with caution)
        # current_admin = await client.get_current_user() 
        # admin_update = UserUpdate(name="Admin User Updated")
        # updated_admin = await client.users.update_current_user(admin_update)
        # print(f"\nUpdated current admin name: {updated_admin.name}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up: Delete the created user
        if new_user_id:
            try:
                print(f"\nDeleting user {new_user_id}...")
                delete_status = await client.users.delete_user(new_user_id)
                print(f"User delete status: {delete_status}")
            except Exception as del_e:
                print(f"Error deleting user {new_user_id}: {del_e}")
        await client.close()

# Run example (Use with caution - requires admin)
# asyncio.run(user_management_examples())
```

#### Admin (`client.admin` - Requires Admin)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup (MUST be an ADMIN user) ---
async def get_admin_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your ADMIN client here
    client = NeoRagClient(base_url="...")
    await client.login("admin@example.com", "admin_password") 
    return client
# ----------------------------------------------------------------------

async def admin_examples():
    # WARNING: Requires admin privileges.
    client = await get_admin_client()
    try:
        # Get system metrics
        metrics = await client.admin.get_system_metrics()
        print("System Metrics:", metrics)

        # Get token usage for the last day
        token_usage = await client.admin.get_token_usage(period="day")
        print("\nToken Usage (last day):", token_usage)

        # Get license status
        license_info = await client.admin.get_license_status()
        print("\nLicense Status:", license_info)

        # Get rate limit statistics
        rate_limits = await client.admin.get_rate_limit_stats()
        print("\nRate Limit Stats:", rate_limits)
        


    finally:
        await client.close()

# Run example (Requires admin)
# asyncio.run(admin_examples())
```

#### Health (`client.health`)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...") # Or use API key
    return client
# ----------------------------------------------

async def health_examples():
    client = await get_authenticated_client()
    try:
        # Simple health check
        simple_health = await client.health.get_health()
        print("Simple Health:", simple_health)

        # Detailed health check
        detailed_health = await client.health.get_detailed_health()
        print("\nDetailed Health:", detailed_health)
        if 'database' in detailed_health.components:
            print(f"  DB Status: {detailed_health.components['database'].status}")

        # Version check
        version_info = await client.health.get_version()
        print("\nVersion Info:", version_info)

        # Database health check
        db_health = await client.health.database_health()
        print("\nDatabase Health:", db_health)

        # Pool health check
        pool_health = await client.health.pool_health()
        print("\nPool Health:", pool_health)

    finally:
        await client.close()

# Run example
# asyncio.run(health_examples())
```

#### Knowledge Graph (`client.knowledge_graph`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, KnowledgeGraphCreate

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

kb_id = UUID("your-knowledge-base-id")
doc_id = UUID("your-document-id")

async def knowledge_graph_examples():
    client = await get_authenticated_client()
    try:
        # Create/retrieve knowledge graph for a knowledge base
        kg = await client.knowledge_graph.create_knowledge_graph(kb_id)
        print(f"Knowledge Graph ID: {kg.id}, Strategy: {kg.extraction_strategy}")

        # Get knowledge graph metadata
        kg_info = await client.knowledge_graph.get_knowledge_graph(kb_id)
        print(f"KG has {kg_info.entity_count} entities, {kg_info.relationship_count} relationships")

        # Process a document to extract entities and relationships
        process_result = await client.knowledge_graph.process_document_for_knowledge_graph(doc_id)
        print(f"Processed: {process_result.entities_extracted} entities, {process_result.relationships_extracted} relationships")

        # Search for entities
        entities = await client.knowledge_graph.search_entities(
            kb_id, query="machine learning", limit=10
        )
        print(f"Found {entities.total} entities matching 'machine learning'")

        # Get relationships for a specific entity
        if entities.entities:
            entity_id = entities.entities[0].id
            relationships = await client.knowledge_graph.get_entity_relationships(
                kb_id, entity_id_str=entity_id
            )
            print(f"Entity has {len(relationships)} relationships")

        # Get full knowledge graph (for visualization)
        full_graph = await client.knowledge_graph.get_full_knowledge_graph(
            kb_id, max_entities=100, max_relationships=200
        )
        print(f"Full graph: {len(full_graph.get('entities', []))} entities")

        # Find paths between two entities
        # paths = await client.knowledge_graph.find_paths_between_entities(
        #     kb_id, "entity_id_1", "entity_id_2", max_depth=3
        # )

    finally:
        await client.close()

# asyncio.run(knowledge_graph_examples())
```

#### RAPTOR (`client.raptor`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

kb_id = UUID("your-knowledge-base-id")

async def raptor_examples():
    client = await get_authenticated_client()
    try:
        # Build a RAPTOR tree for a knowledge base
        tree = await client.raptor.build_tree_for_kb(kb_id)
        print(f"RAPTOR tree created: {tree.id}, Status: {tree.status}")

        # Get tree status
        status = await client.raptor.get_tree_status(kb_id)
        print(f"Tree ready: {status['is_ready']}, Depth: {status.get('current_depth')}")

        # List trees for a knowledge base
        trees = await client.raptor.list_trees_for_kb(kb_id, active_only=True)
        print(f"Found {len(trees)} active RAPTOR trees")

        # Get tree nodes at a specific level
        if trees:
            nodes = await client.raptor.get_tree_nodes(trees[0].id, level=1)
            print(f"Level 1 has {len(nodes)} nodes")

            # Get tree statistics
            stats = await client.raptor.get_tree_statistics(trees[0].id)
            print(f"Tree stats: {stats}")

        # Get system-wide RAPTOR statistics
        system_stats = await client.raptor.get_system_stats()
        print(f"Total RAPTOR trees: {system_stats['total_trees']}")

    finally:
        await client.close()

# asyncio.run(raptor_examples())
```

#### Models (`client.models`)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

async def models_examples():
    client = await get_authenticated_client()
    try:
        # Get available providers
        providers = await client.models.get_providers()
        print(f"Available providers: {providers}")

        # Get models for a provider
        models = await client.models.get_models(provider="openai")
        print(f"OpenAI models: {[m.name for m in models]}")

        # Get embedding models
        embedding_models = await client.models.get_embedding_models()
        print(f"Embedding models: {[m.name for m in embedding_models]}")

        # Get vision-capable models
        vision_models = await client.models.get_vision_models()
        print(f"Vision models: {[m.name for m in vision_models]}")

        # Get model names only
        model_names = await client.models.get_model_names(provider="anthropic")
        print(f"Anthropic model names: {model_names}")

    finally:
        await client.close()

# asyncio.run(models_examples())
```

#### Dashboard (`client.dashboard` - Requires Admin)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup (MUST be an ADMIN user) ---
async def get_admin_client() -> NeoRagClient:
    client = NeoRagClient(base_url="...")
    await client.login("admin@example.com", "admin_password")
    return client
# ----------------------------------------------------------------------

async def dashboard_examples():
    client = await get_admin_client()
    try:
        # Get dashboard metrics
        metrics = await client.dashboard.get_metrics()
        print(f"Total documents: {metrics.get('document_count')}")
        print(f"Total chunks: {metrics.get('chunk_count')}")

        # Get analytics for a time period
        analytics = await client.dashboard.get_analytics(period="30d")
        print(f"Documents created (30d): {analytics.get('documents_created')}")

        # Get documents by MIME type
        pdf_docs = await client.dashboard.get_documents_by_mime_type(
            mime_type="application/pdf", period="7d", limit=20
        )
        print(f"PDF documents (7d): {pdf_docs}")

    finally:
        await client.close()

# asyncio.run(dashboard_examples())
```

#### Webhooks (`client.webhooks`)

```python
import asyncio
from uuid import UUID
from spt_neo_rag_client import NeoRagClient, KnowledgeBaseWebhookConfigUpdate

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

kb_id = UUID("your-knowledge-base-id")

async def webhook_examples():
    client = await get_authenticated_client()
    try:
        # Get current webhook config
        kb_with_webhook = await client.webhooks.get_knowledge_base_webhook_config(kb_id)
        print(f"Current webhook URL: {kb_with_webhook.webhook_url}")

        # Update webhook configuration
        webhook_update = KnowledgeBaseWebhookConfigUpdate(
            webhook_url="https://your-server.com/webhook",
            webhook_secret="your-secret-key",
            is_webhook_enabled=True
        )
        updated_kb = await client.webhooks.update_knowledge_base_webhook_config(
            kb_id, webhook_update
        )
        print(f"Webhook updated: {updated_kb.webhook_url}")

        # Delete (reset) webhook configuration
        # reset_kb = await client.webhooks.delete_knowledge_base_webhook_config(kb_id)

    finally:
        await client.close()

# asyncio.run(webhook_examples())
```

#### Settings (`client.settings` and `client.system_settings`)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient

# --- Public settings (no admin required) ---
async def settings_examples():
    client = NeoRagClient(base_url="...")
    await client.login("...")
    try:
        # Get public settings
        public = await client.settings.get_public_settings()
        print(f"User registration enabled: {public.enable_user_registration}")
    finally:
        await client.close()

# --- System settings (admin required) ---
async def system_settings_examples():
    client = NeoRagClient(base_url="...")
    await client.login("admin@example.com", "admin_password")
    try:
        # Get system settings (API keys are masked)
        settings = await client.system_settings.get_settings()
        print(f"Current settings: {settings}")

        # Update settings
        updated = await client.system_settings.update_settings({
            "default_embedding_model": "text-embedding-3-small"
        })
        print(f"Updated settings: {updated}")

        # List configurations
        configs = await client.system_settings.list_configurations(scope="chunking")
        print(f"Chunking configs: {len(configs)}")

        # Clear settings cache
        await client.system_settings.clear_cache()
        print("Settings cache cleared")

    finally:
        await client.close()

# asyncio.run(settings_examples())
# asyncio.run(system_settings_examples())
```

#### Content (`client.content`)

```python
import asyncio
from spt_neo_rag_client import NeoRagClient

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

async def content_examples():
    client = await get_authenticated_client()
    try:
        # Get content from storage by object path
        content = await client.content.get_content("documents/abc123/file.pdf")
        print(f"Retrieved {len(content)} bytes")

        # Save to file
        with open("downloaded_file.pdf", "wb") as f:
            f.write(content)

    finally:
        await client.close()

# asyncio.run(content_examples())
```

## Access Control with Credentials

The Neo RAG API includes a credential-based access control system that allows you to restrict access to knowledge bases and documents.

### How Credentials Work

-   **Default Access**: By default, resources are created with `["ALL"]` credentials, meaning they're accessible to all users who can authenticate to the API.
-   **Restricted Access**: You can specify custom credentials (e.g., `["team1", "finance"]`) when creating or updating a knowledge base or document to limit who can access it.
-   **Inheritance**: If a document doesn't have specific credentials set, it inherits the credentials from its parent knowledge base.
-   **Access Rules**: A user making a query must provide at least one matching credential in their `credentials` list to access a knowledge base or document that has restricted credentials set. Documents/KBs with `["ALL"]` are always accessible if the user provides `["ALL"]` or any specific credential.

### Setting Credentials

You can set credentials when creating or updating resources:

```python
# Create a knowledge base with restricted access
kb = await client.knowledge_bases.create_knowledge_base(
    KnowledgeBaseCreate(
        name="Finance Knowledge Base",
        description="Financial documents",
        credentials=["finance", "executives"]
    )
)

# Upload a document inheriting KB credentials (assuming kb_id = kb.id)
# await client.documents.upload_document(..., knowledge_base_id=kb_id, credentials=None)

# Upload a document with specific credentials
# await client.documents.upload_document(..., knowledge_base_id=kb_id, credentials=["finance-q2"])

# Update a document's access control
update_data = DocumentUpdate(credentials=["finance"])
doc = await client.documents.update_document(document_id="...", update_data=update_data)
```

### Querying with Credentials

When querying, provide the user's credentials to access restricted resources:

```python
from spt_neo_rag_client import QueryRequest

# Query with specific credentials to access finance/exec documents
query_payload = QueryRequest(
    knowledge_base_ids=[kb.id],
    query="What are our Q2 financial results?",
    credentials=["finance"]  # User only needs one matching credential
)
response = await client.queries.query(query_payload)

# Querying with ["ALL"] will only access unrestricted resources
# or resources explicitly marked with ["ALL"]
query_all = QueryRequest(
    knowledge_base_ids=[kb.id],
    query="General information",
    credentials=["ALL"]  # Might not see finance/exec documents
)
response_all = await client.queries.query(query_all)
```

If the provided credentials don't grant access to any relevant documents or the knowledge base itself, the query might return no sources or raise an error depending on the API configuration.

## Error Handling

The client raises specific exceptions for different error conditions:

-   `NeoRagApiError`: Base exception for API errors (like 4xx or 5xx responses). Contains `status_code` and `detail` attributes.
-   `ConfigurationError`: For issues like missing authentication.
-   `NetworkError`: For connection problems (subclass of `httpx.RequestError`).

```python
from spt_neo_rag_client import NeoRagClient
from spt_neo_rag_client.exceptions import NeoRagApiError, ConfigurationError, NetworkError
from uuid import UUID
import asyncio

# --- Replace with your actual client setup ---
async def get_authenticated_client() -> NeoRagClient:
    # Placeholder: Initialize and authenticate your client here
    client = NeoRagClient(base_url="...")
    await client.login("...")
    return client
# ----------------------------------------------

async def error_handling_example():
    client = await get_authenticated_client()
    try:
        # Example: Try to get a non-existent knowledge base
        invalid_kb_id = UUID("00000000-0000-0000-0000-000000000000")
        kb = await client.knowledge_bases.get_knowledge_base(invalid_kb_id)

    except NeoRagApiError as e:
        print(f"API Error: {e.status_code}")
        print(f"Detail: {e.detail}")
        # Example: Handle specific errors
        if e.status_code == 404:
            print("Resource not found.")
        elif e.status_code == 403:
            print("Permission denied.")
            
    except NetworkError as e:
        print(f"Network Error: Could not connect to the API. {e}")
        
    except ConfigurationError as e:
        print(f"Configuration Error: {e}")
        
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        
    finally:
        await client.close()

# Run example
# asyncio.run(error_handling_example())
```

## License

MIT
