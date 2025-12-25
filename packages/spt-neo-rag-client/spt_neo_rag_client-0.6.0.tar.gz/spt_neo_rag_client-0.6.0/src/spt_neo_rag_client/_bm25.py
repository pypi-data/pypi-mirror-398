"""
BM25 client module for SPT Neo RAG API.
"""

from typing import Any, Dict

from .exceptions import NeoRagApiError


class BM25Endpoints:
    """Client for BM25 index operations."""

    def __init__(self, client):
        """Initialize with reference to the main client."""
        self.client = client

    async def get_bm25_index_status(self, knowledge_base_id: str) -> Dict[str, Any]:
        """
        Get BM25 index status for a knowledge base.
        
        Args:
            knowledge_base_id: The ID of the knowledge base
            
        Returns:
            Dict containing BM25 index status and metadata
            
        Raises:
            NeoRagApiError: If the request fails
        """
        try:
            response = await self.client._request(
                "GET",
                f"bm25/knowledge-bases/{knowledge_base_id}/bm25-index"
            )
            return response.json()
        except Exception as e:
            raise NeoRagApiError(f"Failed to get BM25 index status: {e}") from e

    async def build_bm25_index(
        self, 
        knowledge_base_id: str, 
        k1: float = 1.2, 
        b: float = 0.75
    ) -> Dict[str, Any]:
        """
        Build or rebuild BM25 index for a knowledge base.
        
        Args:
            knowledge_base_id: The ID of the knowledge base
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (field length normalization)
            
        Returns:
            Dict containing build response with task_id
            
        Raises:
            NeoRagApiError: If the request fails
        """
        try:
            data = {
                "k1": k1,
                "b": b
            }
            response = await self.client._request(
                "POST",
                f"bm25/knowledge-bases/{knowledge_base_id}/bm25-index/build",
                json_data=data
            )
            return response.json()
        except Exception as e:
            raise NeoRagApiError(f"Failed to build BM25 index: {e}") from e

    async def delete_bm25_index(self, knowledge_base_id: str) -> Dict[str, Any]:
        """
        Delete BM25 index for a knowledge base.
        
        Args:
            knowledge_base_id: The ID of the knowledge base
            
        Returns:
            Dict containing deletion confirmation
            
        Raises:
            NeoRagApiError: If the request fails
        """
        try:
            response = await self.client._request(
                "DELETE",
                f"bm25/knowledge-bases/{knowledge_base_id}/bm25-index"
            )
            return response.json()
        except Exception as e:
            raise NeoRagApiError(f"Failed to delete BM25 index: {e}") from e

    async def check_bm25_availability(self, knowledge_base_id: str) -> Dict[str, Any]:
        """
        Check if BM25 enhancement is available for a knowledge base.
        
        Args:
            knowledge_base_id: The ID of the knowledge base
            
        Returns:
            Dict containing availability status
            
        Raises:
            NeoRagApiError: If the request fails
        """
        try:
            response = await self.client._request(
                "GET",
                f"bm25/knowledge-bases/{knowledge_base_id}/bm25-index/available"
            )
            return response.json()
        except Exception as e:
            raise NeoRagApiError(f"Failed to check BM25 availability: {e}") from e

    # Sync versions of the methods
    def get_bm25_index_status_sync(self, knowledge_base_id: str) -> Dict[str, Any]:
        """Sync version of get_bm25_index_status."""
        import asyncio
        return asyncio.run(self.get_bm25_index_status(knowledge_base_id))

    def build_bm25_index_sync(
        self, 
        knowledge_base_id: str, 
        k1: float = 1.2, 
        b: float = 0.75
    ) -> Dict[str, Any]:
        """Sync version of build_bm25_index."""
        import asyncio
        return asyncio.run(self.build_bm25_index(knowledge_base_id, k1, b))

    def delete_bm25_index_sync(self, knowledge_base_id: str) -> Dict[str, Any]:
        """Sync version of delete_bm25_index."""
        import asyncio
        return asyncio.run(self.delete_bm25_index(knowledge_base_id))

    def check_bm25_availability_sync(self, knowledge_base_id: str) -> Dict[str, Any]:
        """Sync version of check_bm25_availability."""
        import asyncio
        return asyncio.run(self.check_bm25_availability(knowledge_base_id)) 