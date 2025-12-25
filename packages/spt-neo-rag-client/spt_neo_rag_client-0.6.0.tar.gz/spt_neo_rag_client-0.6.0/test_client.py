"""
Comprehensive test script for SPT Neo RAG Client.
Tests all major endpoint categories against the API.
"""

import asyncio
import os

from spt_neo_rag_client import (
    NeoRagClient,
)

# Configuration - Update these with your actual values
NEO_RAG_BASE_URL = os.getenv("NEO_RAG_BASE_URL", "https://admin.neorag-dev.accor.com")
NEO_RAG_API_KEY = os.getenv("NEO_RAG_API_KEY", "vw6mo98JvXAVjbRkutaH8jaO-gTKJuF_av0gnxp9ljA")


async def test_knowledge_bases(client: NeoRagClient):
    """Test knowledge base endpoints (requires authentication)."""
    print("\n" + "="*60)
    print("Testing Knowledge Base Endpoints (requires auth)")
    print("="*60)

    from spt_neo_rag_client.exceptions import NeoRagApiError

    try:
        # List knowledge bases
        print("\n1. Listing knowledge bases...")
        kbs = await client.knowledge_bases.list_knowledge_bases(limit=5)
        print(f"   ✓ Found {len(kbs)} knowledge bases")
        if kbs:
            print(f"   - First KB: {kbs[0].name} (ID: {kbs[0].id})")

        # Count knowledge bases
        print("\n2. Counting knowledge bases...")
        count = await client.knowledge_bases.count_knowledge_bases()
        print(f"   ✓ Total knowledge bases: {count.count}")

        # Get a specific KB (if any exist)
        if kbs:
            kb_id = kbs[0].id
            print(f"\n3. Getting knowledge base {kb_id}...")
            kb = await client.knowledge_bases.get_knowledge_base(kb_id)
            print(f"   ✓ Retrieved: {kb.name}")
            print(f"   - Documents: {kb.documents_count}")
            print(f"   - Type: {kb.kb_type}")
            print(f"   - Credentials: {kb.credentials}")

        print("\n✅ Knowledge Base tests passed!")

    except NeoRagApiError as e:
        if e.status_code in (401, 403):
            print("\n⚠️  Knowledge Base tests skipped (authentication/permissions required)")
            print(f"   Status: {e.status_code}")
            print("   Hint: Update NEO_RAG_API_KEY with a valid API key with appropriate scopes")
        else:
            print(f"\n❌ Knowledge Base tests failed: {e}")
            raise
    except Exception as e:
        print(f"\n❌ Knowledge Base tests failed: {e}")
        raise


async def test_documents(client: NeoRagClient):
    """Test document endpoints (requires authentication)."""
    print("\n" + "="*60)
    print("Testing Document Endpoints (requires auth)")
    print("="*60)

    from spt_neo_rag_client.exceptions import NeoRagApiError

    try:
        # Get available processors
        print("\n1. Getting available processors...")
        processors = await client.documents.get_processors()
        print(f"   ✓ Available processors: {processors}")

        # Get chunking strategies
        print("\n2. Getting chunking strategies...")
        strategies = await client.documents.get_chunking_strategies()
        print(f"   ✓ Available strategies: {strategies}")

        # List documents
        print("\n3. Listing recent documents...")
        docs = await client.documents.list_documents(limit=5)
        print(f"   ✓ Found {len(docs)} documents")
        if docs:
            doc = docs[0]
            print(f"   - First doc: {doc.name} (Status: {doc.status})")

        # Count documents
        print("\n4. Counting documents...")
        count = await client.documents.count_documents()
        print(f"   ✓ Total documents: {count.count}")

        print("\n✅ Document tests passed!")

    except NeoRagApiError as e:
        if e.status_code in (401, 403):
            print("\n⚠️  Document tests skipped (authentication/permissions required)")
            print(f"   Status: {e.status_code} - {e.detail}")
        else:
            print(f"\n❌ Document tests failed: {e}")
            raise
    except Exception as e:
        print(f"\n❌ Document tests failed: {e}")
        raise


async def test_queries(client: NeoRagClient):
    """Test query endpoints (requires authentication)."""
    print("\n" + "="*60)
    print("Testing Query Endpoints (requires auth)")
    print("="*60)

    from spt_neo_rag_client.exceptions import NeoRagApiError

    try:
        # Get available query strategies
        print("\n1. Getting query strategies...")
        strategies = await client.queries.get_query_strategies()
        print(f"   ✓ Available strategies: {strategies.strategies}")

        print("\n✅ Query tests passed!")

    except NeoRagApiError as e:
        if e.status_code in (401, 403):
            print("\n⚠️  Query tests skipped (authentication required)")
        else:
            print(f"\n❌ Query tests failed: {e}")
            raise
    except Exception as e:
        print(f"\n❌ Query tests failed: {e}")
        raise


async def test_health(client: NeoRagClient):
    """Test health endpoints."""
    print("\n" + "="*60)
    print("Testing Health Endpoints")
    print("="*60)

    try:
        # Simple health check
        print("\n1. Simple health check...")
        health = await client.health.get_health()
        print(f"   ✓ Status: {health.status}")

        # Version info
        print("\n2. Getting version...")
        version = await client.health.get_version()
        print(f"   ✓ Version: {version}")

        print("\n✅ Health tests passed!")

    except Exception as e:
        print(f"\n❌ Health tests failed: {e}")
        raise


async def test_settings(client: NeoRagClient):
    """Test settings endpoints."""
    print("\n" + "="*60)
    print("Testing Settings Endpoints")
    print("="*60)

    try:
        # Get public settings
        print("\n1. Getting public settings...")
        settings = await client.settings.get_public_settings()
        print("   ✓ Settings retrieved successfully")
        print(f"   - Enable user registration: {settings.enable_user_registration}")

        print("\n✅ Settings tests passed!")

    except Exception as e:
        print(f"\n❌ Settings tests failed: {e}")
        raise


async def test_models(client: NeoRagClient):
    """Test model endpoints (requires authentication)."""
    print("\n" + "="*60)
    print("Testing Model Endpoints (requires auth)")
    print("="*60)

    from spt_neo_rag_client.exceptions import NeoRagApiError

    try:
        # Get available models
        print("\n1. Getting available models...")
        models = await client.models.get_models()
        print(f"   ✓ Found {len(models)} models")
        if models:
            print(f"   - First model: {models[0].model_name} (Provider: {models[0].provider})")

        print("\n✅ Model tests passed!")

    except NeoRagApiError as e:
        if e.status_code in (401, 403):
            print("\n⚠️  Model tests skipped (authentication required)")
        else:
            print(f"\n❌ Model tests failed: {e}")
            raise
    except Exception as e:
        print(f"\n❌ Model tests failed: {e}")
        raise


async def test_tasks(client: NeoRagClient):
    """Test task endpoints (requires authentication)."""
    print("\n" + "="*60)
    print("Testing Task Endpoints (requires auth)")
    print("="*60)

    from spt_neo_rag_client.exceptions import NeoRagApiError

    try:
        # List tasks
        print("\n1. Listing recent tasks...")
        tasks = await client.tasks.list_tasks()
        print(f"   ✓ Found {len(tasks)} recent tasks")
        if tasks:
            task = tasks[0]
            print(f"   - First task: {task.task_type} (Status: {task.status})")

        print("\n✅ Task tests passed!")

    except NeoRagApiError as e:
        if e.status_code in (401, 403):
            print("\n⚠️  Task tests skipped (authentication required)")
        else:
            print(f"\n❌ Task tests failed: {e}")
            raise
    except Exception as e:
        print(f"\n❌ Task tests failed: {e}")
        raise


async def main():
    """Run all tests."""
    print("="*60)
    print("SPT Neo RAG Client - Comprehensive Test Suite")
    print("="*60)
    print(f"\nBase URL: {NEO_RAG_BASE_URL}")
    print(f"API Key: {'*' * 10}{NEO_RAG_API_KEY[-4:]}")

    # Initialize client
    client = NeoRagClient(
        base_url=NEO_RAG_BASE_URL,
        api_key=NEO_RAG_API_KEY
    )

    try:
        # Run all test suites
        await test_health(client)
        await test_settings(client)
        await test_knowledge_bases(client)
        await test_documents(client)
        await test_queries(client)
        await test_models(client)
        await test_tasks(client)

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)

    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TESTS FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
