"""API Key endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import Any, Callable, Coroutine, List
from uuid import UUID

from .models import (
    ApiKeyCreate,
    ApiKeyFullResponse,
    ApiKeyResponse,
    ApiKeyUpdate,
    GenericStatusResponse,
)

# Type alias for the request function
RequestFunc = Callable[..., Coroutine[Any, Any, Any]]


class ApiKeyEndpoints:
    """Handles API key-related API operations for the current user."""

    def __init__(self, request_func: RequestFunc):
        self._request = request_func

    async def list_api_keys(
        self, skip: int = 0, limit: int = 100
    ) -> List[ApiKeyResponse]:
        """
        List API keys for the current user.

        Args:
            skip: Number of keys to skip.
            limit: Maximum number of keys to return.
            
        Returns:
            List[ApiKeyResponse]: List of API keys.
        """
        params = {"skip": skip, "limit": limit}
        response = await self._request("GET", "/api-keys", params=params)
        return [ApiKeyResponse(**item) for item in response.json()]

    def list_api_keys_sync(
        self, skip: int = 0, limit: int = 100
    ) -> List[ApiKeyResponse]:
        """Synchronous version of list_api_keys."""
        return asyncio.run(self.list_api_keys(skip, limit))

    async def create_api_key(
        self, create_data: ApiKeyCreate
    ) -> ApiKeyFullResponse:
        """
        Create a new API key for the current user.
        The full key is only available in this response.

        Args:
            create_data: ApiKeyCreate model with key details.
            
        Returns:
            ApiKeyFullResponse: Created key details including the full key.
        """
        response = await self._request(
            "POST", "/api-keys", json_data=create_data.model_dump(mode="json")
        )
        return ApiKeyFullResponse(**response.json())

    def create_api_key_sync(
        self, create_data: ApiKeyCreate
    ) -> ApiKeyFullResponse:
        """Synchronous version of create_api_key."""
        return asyncio.run(self.create_api_key(create_data))

    async def get_api_key(self, api_key_id: UUID) -> ApiKeyResponse:
        """
        Get details for a specific API key by ID.

        Args:
            api_key_id: ID of the API key.
            
        Returns:
            ApiKeyResponse: API key details (without the full key).
        """
        response = await self._request("GET", f"/api-keys/{api_key_id}")
        return ApiKeyResponse(**response.json())

    def get_api_key_sync(self, api_key_id: UUID) -> ApiKeyResponse:
        """Synchronous version of get_api_key."""
        return asyncio.run(self.get_api_key(api_key_id))

    async def update_api_key(
        self, api_key_id: UUID, update_data: ApiKeyUpdate
    ) -> ApiKeyResponse:
        """
        Update an API key (e.g., name, status, expiration).
        Uses PATCH method.

        Args:
            api_key_id: ID of the key to update.
            update_data: ApiKeyUpdate model with fields to change.
            
        Returns:
            ApiKeyResponse: Updated API key details.
        """
        response = await self._request(
            "PATCH", # Changed from PUT to PATCH
            f"/api-keys/{api_key_id}",
            json_data=update_data.model_dump(mode="json", exclude_unset=True),
        )
        return ApiKeyResponse(**response.json())

    def update_api_key_sync(
        self, api_key_id: UUID, update_data: ApiKeyUpdate
    ) -> ApiKeyResponse:
        """Synchronous version of update_api_key."""
        return asyncio.run(self.update_api_key(api_key_id, update_data))

    async def delete_api_key(self, api_key_id: UUID) -> GenericStatusResponse:
        """
        Delete a specific API key by ID.

        Args:
            api_key_id: ID of the key to delete.
            
        Returns:
            GenericStatusResponse: Confirmation message.
        """
        response = await self._request("DELETE", f"/api-keys/{api_key_id}")
        return GenericStatusResponse(**response.json())

    def delete_api_key_sync(self, api_key_id: UUID) -> GenericStatusResponse:
        """Synchronous version of delete_api_key."""
        return asyncio.run(self.delete_api_key(api_key_id)) 