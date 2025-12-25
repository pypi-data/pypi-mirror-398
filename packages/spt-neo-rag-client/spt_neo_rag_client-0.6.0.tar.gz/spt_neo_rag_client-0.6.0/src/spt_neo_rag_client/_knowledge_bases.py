"""Knowledge Base endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List
from uuid import UUID

from .models import (
    CountResponse,
    KnowledgeBaseConfigUpdate,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)

# Type alias for the request function
RequestFunc = Callable[..., Coroutine[Any, Any, Any]]


class KnowledgeBaseEndpoints:
    """Handles knowledge base-related API operations."""

    def __init__(self, request_func: RequestFunc):
        self._request = request_func

    async def create_knowledge_base(
        self, create_data: KnowledgeBaseCreate
    ) -> KnowledgeBaseResponse:
        """
        Create a new knowledge base.

        Args:
            create_data: KnowledgeBaseCreate model with KB details.
            
        Returns:
            KnowledgeBaseResponse: Created knowledge base details.
        """
        response = await self._request(
            "POST", "/knowledge-bases", json_data=create_data.model_dump(mode="json")
        )
        return KnowledgeBaseResponse(**response.json())

    def create_knowledge_base_sync(
        self, create_data: KnowledgeBaseCreate
    ) -> KnowledgeBaseResponse:
        """Synchronous version of create_knowledge_base."""
        return asyncio.run(self.create_knowledge_base(create_data))

    async def list_knowledge_bases(
        self, skip: int = 0, limit: int = 100
    ) -> List[KnowledgeBaseResponse]:
        """
        List knowledge bases.

        Args:
            skip: Number of KBs to skip.
            limit: Maximum number of KBs to return.
            
        Returns:
            List[KnowledgeBaseResponse]: List of knowledge bases.
        """
        params = {"skip": skip, "limit": limit}
        response = await self._request("GET", "/knowledge-bases", params=params)
        return [KnowledgeBaseResponse(**item) for item in response.json()]

    def list_knowledge_bases_sync(
        self, skip: int = 0, limit: int = 100
    ) -> List[KnowledgeBaseResponse]:
        """Synchronous version of list_knowledge_bases."""
        return asyncio.run(self.list_knowledge_bases(skip, limit))

    async def count_knowledge_bases(self) -> CountResponse:
        """
        Get the total count of knowledge bases.
        
        Returns:
            CountResponse: The total count.
        """
        response = await self._request("GET", "/knowledge-bases/count")
        # Endpoint returns an int directly
        return CountResponse(count=response.json())

    def count_knowledge_bases_sync(self) -> CountResponse:
        """Synchronous version of count_knowledge_bases."""
        return asyncio.run(self.count_knowledge_bases())

    async def get_knowledge_base(self, kb_id: UUID) -> KnowledgeBaseResponse:
        """
        Get details for a specific knowledge base.

        Args:
            kb_id: ID of the knowledge base.
            
        Returns:
            KnowledgeBaseResponse: Knowledge base details.
        """
        response = await self._request("GET", f"/knowledge-bases/{kb_id}")
        return KnowledgeBaseResponse(**response.json())

    def get_knowledge_base_sync(self, kb_id: UUID) -> KnowledgeBaseResponse:
        """Synchronous version of get_knowledge_base."""
        return asyncio.run(self.get_knowledge_base(kb_id))

    async def update_knowledge_base(
        self, kb_id: UUID, update_data: KnowledgeBaseUpdate
    ) -> KnowledgeBaseResponse:
        """
        Update details for a specific knowledge base.

        Args:
            kb_id: ID of the knowledge base to update.
            update_data: KnowledgeBaseUpdate model with fields to update.
            
        Returns:
            KnowledgeBaseResponse: Updated knowledge base details.
        """
        response = await self._request(
            "PUT",
            f"/knowledge-bases/{kb_id}",
            json_data=update_data.model_dump(mode="json", exclude_unset=True),
        )
        return KnowledgeBaseResponse(**response.json())

    def update_knowledge_base_sync(
        self, kb_id: UUID, update_data: KnowledgeBaseUpdate
    ) -> KnowledgeBaseResponse:
        """Synchronous version of update_knowledge_base."""
        return asyncio.run(self.update_knowledge_base(kb_id, update_data))

    async def update_knowledge_base_config(
        self, kb_id: UUID, config_data: KnowledgeBaseConfigUpdate
    ) -> KnowledgeBaseResponse:
        """
        Update the configuration for a specific knowledge base.

        Args:
            kb_id: ID of the knowledge base.
            config_data: KnowledgeBaseConfigUpdate model with the new config.
            
        Returns:
            KnowledgeBaseResponse: Updated knowledge base details.
        """
        response = await self._request(
            "PATCH",
            f"/knowledge-bases/{kb_id}/config",
            json_data=config_data.model_dump(mode="json"),
        )
        return KnowledgeBaseResponse(**response.json())

    def update_knowledge_base_config_sync(
        self, kb_id: UUID, config_data: KnowledgeBaseConfigUpdate
    ) -> KnowledgeBaseResponse:
        """Synchronous version of update_knowledge_base_config."""
        return asyncio.run(self.update_knowledge_base_config(kb_id, config_data))

    async def delete_knowledge_base(self, kb_id: UUID) -> Dict[str, Any]:
        """
        Delete a specific knowledge base.

        Args:
            kb_id: ID of the knowledge base to delete.
            
        Returns:
            Dict[str, Any]: Confirmation message (or None on 204).
        """
        response = await self._request("DELETE", f"/knowledge-bases/{kb_id}")
        # Returns 204 No Content on success
        if response.status_code == 204:
            return {"status": "success", "message": f"Knowledge Base {kb_id} deleted."}
        return response.json() # Should ideally not happen on success

    def delete_knowledge_base_sync(self, kb_id: UUID) -> Dict[str, Any]:
        """Synchronous version of delete_knowledge_base."""
        return asyncio.run(self.delete_knowledge_base(kb_id))

    async def get_embedding_models(self, provider: str) -> List[str]:
        """
        Get available embedding models for a specific provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic').

        Returns:
            List[str]: List of available embedding model names.
        """
        params = {"provider": provider}
        response = await self._request("GET", "/models/embedding/list", params=params)
        return response.json()

    def get_embedding_models_sync(self, provider: str) -> List[str]:
        """Synchronous version of get_embedding_models."""
        return asyncio.run(self.get_embedding_models(provider))
