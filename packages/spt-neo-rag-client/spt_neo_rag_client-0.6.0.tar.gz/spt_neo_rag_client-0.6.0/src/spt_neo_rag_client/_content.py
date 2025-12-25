"""Content endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import NeoRagClient


class ContentEndpoints:
    """Handles content-related API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def get_content(self, object_name: str) -> bytes:
        """
        Get content securely from storage via streaming.

        Args:
            object_name: Full path within the bucket (e.g., dir/subdir/file.ext).
            
        Returns:
            bytes: Raw content of the object.
        """
        response = await self._client._request("GET", f"/content/{object_name}")
        return response.content

    def get_content_sync(self, object_name: str) -> bytes:
        """Synchronous version of get_content."""
        return asyncio.run(self.get_content(object_name)) 