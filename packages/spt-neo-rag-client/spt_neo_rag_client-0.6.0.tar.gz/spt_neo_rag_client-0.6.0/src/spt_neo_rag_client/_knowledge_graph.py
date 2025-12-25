"""Knowledge Graph endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from .models import (
    GenericStatusResponse,
    KGPathSegment,
    KGProcessedDocumentResponse,
    KGRelationshipDetailResponse,
    KnowledgeGraphCreate,
    KnowledgeGraphResponse,
    KnowledgeGraphUpdate,
    PaginatedKGEntityResponse,
)

if TYPE_CHECKING:
    from .client import NeoRagClient


class KnowledgeGraphEndpoints:
    """Handles knowledge graph-related API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def create_knowledge_graph(
        self, knowledge_base_id: UUID, create_data: Optional[KnowledgeGraphCreate] = None
    ) -> KnowledgeGraphResponse:
        """
        Create or retrieve existing knowledge graph metadata for a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            create_data: Optional creation data. If None, uses defaults.
            
        Returns:
            KnowledgeGraphResponse: Knowledge graph metadata.
        """
        json_data = create_data.model_dump(mode="json", by_alias=True) if create_data else None
        response = await self._client._request(
            "POST", 
            f"/knowledge-bases/{knowledge_base_id}/knowledge-graph",
            json_data=json_data
        )
        return KnowledgeGraphResponse(**response.json())

    def create_knowledge_graph_sync(
        self, knowledge_base_id: UUID, create_data: Optional[KnowledgeGraphCreate] = None
    ) -> KnowledgeGraphResponse:
        """Synchronous version of create_knowledge_graph."""
        return asyncio.run(self.create_knowledge_graph(knowledge_base_id, create_data))

    async def get_knowledge_graph(self, knowledge_base_id: UUID) -> KnowledgeGraphResponse:
        """
        Get knowledge graph metadata for a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            KnowledgeGraphResponse: Knowledge graph metadata.
        """
        response = await self._client._request(
            "GET", f"/knowledge-bases/{knowledge_base_id}/knowledge-graph"
        )
        return KnowledgeGraphResponse(**response.json())

    def get_knowledge_graph_sync(self, knowledge_base_id: UUID) -> KnowledgeGraphResponse:
        """Synchronous version of get_knowledge_graph."""
        return asyncio.run(self.get_knowledge_graph(knowledge_base_id))

    async def update_knowledge_graph(
        self, knowledge_base_id: UUID, update_data: KnowledgeGraphUpdate
    ) -> KnowledgeGraphResponse:
        """
        Update knowledge graph metadata for a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            update_data: Update data.
            
        Returns:
            KnowledgeGraphResponse: Updated knowledge graph metadata.
        """
        response = await self._client._request(
            "PUT",
            f"/knowledge-bases/{knowledge_base_id}/knowledge-graph",
            json_data=update_data.model_dump(mode="json", exclude_unset=True, by_alias=True),
        )
        return KnowledgeGraphResponse(**response.json())

    def update_knowledge_graph_sync(
        self, knowledge_base_id: UUID, update_data: KnowledgeGraphUpdate
    ) -> KnowledgeGraphResponse:
        """Synchronous version of update_knowledge_graph."""
        return asyncio.run(self.update_knowledge_graph(knowledge_base_id, update_data))

    async def delete_knowledge_graph(self, knowledge_base_id: UUID) -> GenericStatusResponse:
        """
        Delete knowledge graph metadata and all associated graph data.

        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            GenericStatusResponse: Confirmation message.
        """
        response = await self._client._request(
            "DELETE", f"/knowledge-bases/{knowledge_base_id}/knowledge-graph"
        )
        return GenericStatusResponse(**response.json())

    def delete_knowledge_graph_sync(self, knowledge_base_id: UUID) -> GenericStatusResponse:
        """Synchronous version of delete_knowledge_graph."""
        return asyncio.run(self.delete_knowledge_graph(knowledge_base_id))

    async def process_document_for_knowledge_graph(
        self, document_id: UUID, force_reprocess: bool = False
    ) -> KGProcessedDocumentResponse:
        """
        Process a document to extract entities and relationships for the knowledge graph.

        Args:
            document_id: ID of the document to process.
            force_reprocess: Force reprocessing even if already processed.
            
        Returns:
            KGProcessedDocumentResponse: Processing results.
        """
        params = {"force_reprocess": force_reprocess}
        response = await self._client._request(
            "POST", f"/documents/{document_id}/process-knowledge-graph", params=params
        )
        return KGProcessedDocumentResponse(**response.json())

    def process_document_for_knowledge_graph_sync(
        self, document_id: UUID, force_reprocess: bool = False
    ) -> KGProcessedDocumentResponse:
        """Synchronous version of process_document_for_knowledge_graph."""
        return asyncio.run(self.process_document_for_knowledge_graph(document_id, force_reprocess))

    async def search_entities(
        self,
        knowledge_base_id: UUID,
        query: str = "",
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedKGEntityResponse:
        """
        Search for entities in the knowledge graph.

        Args:
            knowledge_base_id: ID of the knowledge base.
            query: Text query to search for entities.
            entity_type: Optional entity type to filter by.
            skip: Number of entities to skip for pagination.
            limit: Maximum number of entities to return.
            
        Returns:
            PaginatedKGEntityResponse: Search results with pagination.
        """
        params = {"query": query, "skip": skip, "limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
            
        response = await self._client._request(
            "GET", f"/knowledge-bases/{knowledge_base_id}/entities", params=params
        )
        return PaginatedKGEntityResponse(**response.json())

    def search_entities_sync(
        self,
        knowledge_base_id: UUID,
        query: str = "",
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedKGEntityResponse:
        """Synchronous version of search_entities."""
        return asyncio.run(self.search_entities(knowledge_base_id, query, entity_type, skip, limit))

    async def get_entity_relationships(
        self,
        knowledge_base_id: UUID,
        entity_id_str: str,
        relationship_types: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[KGRelationshipDetailResponse]:
        """
        Get relationships for a specific entity.

        Args:
            knowledge_base_id: ID of the knowledge base.
            entity_id_str: String ID of the entity.
            relationship_types: Optional list of relationship types to filter by.
            limit: Maximum number of relationships to return.
            
        Returns:
            List[KGRelationshipDetailResponse]: Entity relationships.
        """
        params = {"limit": limit}
        if relationship_types:
            params["relationship_types"] = relationship_types
            
        response = await self._client._request(
            "GET",
            f"/knowledge-bases/{knowledge_base_id}/entities/{entity_id_str}/relationships",
            params=params,
        )
        return [KGRelationshipDetailResponse(**item) for item in response.json()]

    def get_entity_relationships_sync(
        self,
        knowledge_base_id: UUID,
        entity_id_str: str,
        relationship_types: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[KGRelationshipDetailResponse]:
        """Synchronous version of get_entity_relationships."""
        return asyncio.run(self.get_entity_relationships(knowledge_base_id, entity_id_str, relationship_types, limit))

    async def get_full_knowledge_graph(
        self,
        knowledge_base_id: UUID,
        max_entities: int = 500,
        max_relationships: int = 1000,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get the full knowledge graph for a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.
            max_entities: Maximum number of entities to return.
            max_relationships: Maximum number of relationships to return.
            entity_types: Optional list of entity types to filter by.
            relationship_types: Optional list of relationship types to filter by.
            
        Returns:
            Dict[str, Any]: Full knowledge graph data.
        """
        params = {
            "max_entities": max_entities,
            "max_relationships": max_relationships,
        }
        if entity_types:
            params["entity_types"] = entity_types
        if relationship_types:
            params["relationship_types"] = relationship_types
            
        response = await self._client._request(
            "GET", f"/knowledge-bases/{knowledge_base_id}/full-graph", params=params
        )
        return response.json()

    def get_full_knowledge_graph_sync(
        self,
        knowledge_base_id: UUID,
        max_entities: int = 500,
        max_relationships: int = 1000,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Synchronous version of get_full_knowledge_graph."""
        return asyncio.run(self.get_full_knowledge_graph(
            knowledge_base_id, max_entities, max_relationships, entity_types, relationship_types
        ))

    async def find_paths_between_entities(
        self,
        knowledge_base_id: UUID,
        source_entity_id_str: str,
        target_entity_id_str: str,
        max_depth: int = 3,
    ) -> List[List[KGPathSegment]]:
        """
        Find paths between two entities in the knowledge graph.

        Args:
            knowledge_base_id: ID of the knowledge base.
            source_entity_id_str: String ID of the source entity.
            target_entity_id_str: String ID of the target entity.
            max_depth: Maximum depth of paths to search.
            
        Returns:
            List[List[KGPathSegment]]: List of paths between entities.
        """
        params = {"max_depth": max_depth}
        response = await self._client._request(
            "GET",
            f"/knowledge-bases/{knowledge_base_id}/paths/from/{source_entity_id_str}/to/{target_entity_id_str}",
            params=params,
        )
        return [[KGPathSegment(**segment) for segment in path] for path in response.json()]

    def find_paths_between_entities_sync(
        self,
        knowledge_base_id: UUID,
        source_entity_id_str: str,
        target_entity_id_str: str,
        max_depth: int = 3,
    ) -> List[List[KGPathSegment]]:
        """Synchronous version of find_paths_between_entities."""
        return asyncio.run(self.find_paths_between_entities(
            knowledge_base_id, source_entity_id_str, target_entity_id_str, max_depth
        )) 