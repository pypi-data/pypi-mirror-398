"""
RAPTOR endpoints for the SPT Neo RAG Client.

This module provides methods for managing RAPTOR (Recursive Abstractive Processing
for Tree-Organized Retrieval) trees and nodes.
"""

from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from pydantic import TypeAdapter

from .models import (
    RaptorNodeResponse,
    RaptorTreeCreate,
    RaptorTreeResponse,
    RaptorTreeUpdate,
)


class RaptorEndpoints:
    """Endpoints for RAPTOR tree operations."""

    def __init__(self, request_func: Callable):
        """
        Initialize RAPTOR endpoints.

        Args:
            request_func: The client's _request method for making API calls
        """
        self._request = request_func

    async def create_tree(
        self,
        knowledge_base_id: UUID,
        max_depth: int = 3,
        cluster_size: int = 10,
        summary_length: int = 200,
        clustering_config: Optional[Dict[str, Any]] = None,
        summarization_config: Optional[Dict[str, Any]] = None,
    ) -> RaptorTreeResponse:
        """
        Create a new RAPTOR tree for a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base
            max_depth: Maximum depth of the tree (default: 3)
            cluster_size: Target cluster size (default: 10)
            summary_length: Target summary length in tokens (default: 200)
            clustering_config: Optional clustering configuration
            summarization_config: Optional summarization configuration

        Returns:
            RaptorTreeResponse: Created RAPTOR tree
        """
        tree_data = RaptorTreeCreate(
            knowledge_base_id=knowledge_base_id,
            max_depth=max_depth,
            cluster_size=cluster_size,
            summary_length=summary_length,
            clustering_config=clustering_config,
            summarization_config=summarization_config,
        )
        response = await self._request(
            "POST",
            "/raptor/trees",
            json_data=tree_data.model_dump(mode="json", exclude_none=True),
        )
        return RaptorTreeResponse(**response.json())

    async def get_tree(self, tree_id: UUID) -> RaptorTreeResponse:
        """
        Get a RAPTOR tree by ID.

        Args:
            tree_id: ID of the RAPTOR tree

        Returns:
            RaptorTreeResponse: RAPTOR tree information
        """
        response = await self._request("GET", f"/raptor/trees/{tree_id}")
        return RaptorTreeResponse(**response.json())

    async def list_trees_for_kb(
        self, kb_id: UUID, active_only: bool = True
    ) -> List[RaptorTreeResponse]:
        """
        Get all RAPTOR trees for a knowledge base.

        Args:
            kb_id: ID of the knowledge base
            active_only: Only return active trees (default: True)

        Returns:
            List[RaptorTreeResponse]: List of RAPTOR trees
        """
        params = {"active_only": active_only}
        response = await self._request(
            "GET", f"/raptor/knowledge-bases/{kb_id}/trees", params=params
        )

        adapter = TypeAdapter(List[RaptorTreeResponse])
        return adapter.validate_python(response.json())

    async def update_tree(
        self, tree_id: UUID, tree_update: RaptorTreeUpdate
    ) -> RaptorTreeResponse:
        """
        Update a RAPTOR tree.

        Args:
            tree_id: ID of the RAPTOR tree
            tree_update: Update data

        Returns:
            RaptorTreeResponse: Updated RAPTOR tree
        """
        response = await self._request(
            "PUT",
            f"/raptor/trees/{tree_id}",
            json_data=tree_update.model_dump(mode="json", exclude_none=True),
        )
        return RaptorTreeResponse(**response.json())

    async def delete_tree(self, tree_id: UUID) -> Dict[str, Any]:
        """
        Delete a RAPTOR tree.

        Args:
            tree_id: ID of the RAPTOR tree

        Returns:
            Dict[str, Any]: Deletion confirmation message
        """
        response = await self._request("DELETE", f"/raptor/trees/{tree_id}")
        return response.json()

    async def rebuild_tree(
        self, tree_id: UUID, config: Optional[Dict[str, Any]] = None
    ) -> RaptorTreeResponse:
        """
        Rebuild a RAPTOR tree.

        Args:
            tree_id: ID of the RAPTOR tree
            config: Optional rebuild configuration

        Returns:
            RaptorTreeResponse: Updated RAPTOR tree
        """
        json_data = {"config": config} if config else {}
        response = await self._request(
            "POST", f"/raptor/trees/{tree_id}/rebuild", json_data=json_data
        )
        return RaptorTreeResponse(**response.json())

    async def get_tree_nodes(
        self, tree_id: UUID, level: Optional[int] = None
    ) -> List[RaptorNodeResponse]:
        """
        Get nodes from a RAPTOR tree.

        Args:
            tree_id: ID of the RAPTOR tree
            level: Optional filter by tree level

        Returns:
            List[RaptorNodeResponse]: List of RAPTOR nodes
        """
        params = {}
        if level is not None:
            params["level"] = level

        response = await self._request(
            "GET", f"/raptor/trees/{tree_id}/nodes", params=params
        )

        adapter = TypeAdapter(List[RaptorNodeResponse])
        return adapter.validate_python(response.json())

    async def get_tree_statistics(self, tree_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about a RAPTOR tree.

        Args:
            tree_id: ID of the RAPTOR tree

        Returns:
            Dict[str, Any]: Tree statistics
        """
        response = await self._request("GET", f"/raptor/trees/{tree_id}/statistics")
        return response.json()

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get aggregate RAPTOR statistics for the system.

        Returns:
            Dict[str, Any]: System-wide RAPTOR statistics
        """
        response = await self._request("GET", "/raptor/stats")
        return response.json()

    async def get_kb_stats(self, kb_id: UUID) -> Dict[str, Any]:
        """
        Get RAPTOR statistics for a specific knowledge base.

        Args:
            kb_id: ID of the knowledge base

        Returns:
            Dict[str, Any]: Knowledge base RAPTOR statistics
        """
        response = await self._request("GET", f"/raptor/knowledge-bases/{kb_id}/stats")
        return response.json()

    async def build_tree_for_kb(
        self, kb_id: UUID, config: Optional[Dict[str, Any]] = None
    ) -> RaptorTreeResponse:
        """
        Build a RAPTOR tree for a knowledge base.

        Args:
            kb_id: ID of the knowledge base
            config: Optional build configuration

        Returns:
            RaptorTreeResponse: Created RAPTOR tree
        """
        json_data = {"config": config} if config else {}
        response = await self._request(
            "POST", f"/raptor/knowledge-bases/{kb_id}/build-tree", json_data=json_data
        )
        return RaptorTreeResponse(**response.json())

    async def get_tree_status(self, kb_id: UUID) -> Dict[str, Any]:
        """
        Get the status of RAPTOR tree for a knowledge base.

        Args:
            kb_id: ID of the knowledge base

        Returns:
            Dict[str, Any]: Tree status information
        """
        response = await self._request(
            "GET", f"/raptor/knowledge-bases/{kb_id}/tree-status"
        )
        return response.json()
