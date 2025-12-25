"""Webhook endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

from .models import (
    KnowledgeBaseResponse,
    KnowledgeBaseWebhookConfigUpdate,
)

if TYPE_CHECKING:
    from .client import NeoRagClient


class WebhookEndpoints:
    """Handles webhook-related API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def get_knowledge_base_webhook_config(
        self, knowledge_base_id: UUID
    ) -> KnowledgeBaseResponse:
        """
        Get webhook configuration for a specific knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            KnowledgeBaseResponse: Knowledge base with webhook configuration.
        """
        response = await self._client._request(
            "GET", f"/webhooks/knowledge_bases/{knowledge_base_id}"
        )
        return KnowledgeBaseResponse(**response.json())

    def get_knowledge_base_webhook_config_sync(
        self, knowledge_base_id: UUID
    ) -> KnowledgeBaseResponse:
        """Synchronous version of get_knowledge_base_webhook_config."""
        return asyncio.run(self.get_knowledge_base_webhook_config(knowledge_base_id))

    async def update_knowledge_base_webhook_config(
        self, knowledge_base_id: UUID, webhook_data: KnowledgeBaseWebhookConfigUpdate
    ) -> KnowledgeBaseResponse:
        """
        Update webhook configuration for a specific knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            webhook_data: Webhook configuration update data.
            
        Returns:
            KnowledgeBaseResponse: Updated knowledge base with webhook configuration.
        """
        response = await self._client._request(
            "PATCH",
            f"/webhooks/knowledge_bases/{knowledge_base_id}",
            json_data=webhook_data.model_dump(mode="json", exclude_unset=True),
        )
        return KnowledgeBaseResponse(**response.json())

    def update_knowledge_base_webhook_config_sync(
        self, knowledge_base_id: UUID, webhook_data: KnowledgeBaseWebhookConfigUpdate
    ) -> KnowledgeBaseResponse:
        """Synchronous version of update_knowledge_base_webhook_config."""
        return asyncio.run(self.update_knowledge_base_webhook_config(knowledge_base_id, webhook_data))

    async def delete_knowledge_base_webhook_config(
        self, knowledge_base_id: UUID
    ) -> KnowledgeBaseResponse:
        """
        Delete (reset) webhook configuration for a specific knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            KnowledgeBaseResponse: Knowledge base with reset webhook configuration.
        """
        response = await self._client._request(
            "DELETE", f"/webhooks/knowledge_bases/{knowledge_base_id}"
        )
        return KnowledgeBaseResponse(**response.json())

    def delete_knowledge_base_webhook_config_sync(
        self, knowledge_base_id: UUID
    ) -> KnowledgeBaseResponse:
        """Synchronous version of delete_knowledge_base_webhook_config."""
        return asyncio.run(self.delete_knowledge_base_webhook_config(knowledge_base_id)) 