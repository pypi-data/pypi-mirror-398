"""Model endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from .models import (
    ModelCreateRequest,
    ModelDeleteResponse,
    ModelInfo,
    ModelUpdateRequest,
)

if TYPE_CHECKING:
    from .client import NeoRagClient


class ModelEndpoints:
    """Handles model-related API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def _get(self, path: str, params: Optional[dict] = None) -> List[ModelInfo]:
        response = await self._client._request("GET", path, params=params)
        return [ModelInfo(**item) for item in response.json()]

    async def get_models(
        self,
        provider: Optional[str] = None,
        model_type: Optional[str] = None,
        has_vision: Optional[bool] = None
    ) -> List[ModelInfo]:
        """
        Get available models for a specific provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic').
            model_type: Optional model type filter (e.g., 'embedding', 'chat').
            has_vision: Optional filter for vision-capable models.

        Returns:
            List[ModelInfo]: List of available models.
        """
        params: dict = {}
        if provider:
            params["provider"] = provider
        if model_type:
            params["type"] = model_type
        if has_vision is not None:
            params["has_vision"] = has_vision

        return await self._get("/models/list", params=params or None)

    def get_models_sync(
        self, provider: str, model_type: Optional[str] = None
    ) -> List[ModelInfo]:
        """Synchronous version of get_models."""
        return asyncio.run(self.get_models(provider, model_type))

    async def get_model_names(
        self,
        provider: str,
        model_type: Optional[str] = None,
        has_vision: Optional[bool] = None
    ) -> List[str]:
        """
        Get available model names for a specific provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic').
            model_type: Optional model type filter (e.g., 'embedding', 'chat').
            has_vision: Optional filter for vision-capable models.

        Returns:
            List[str]: List of available model names.
        """
        params = {"provider": provider}
        if model_type:
            params["type"] = model_type
        if has_vision is not None:
            params["has_vision"] = has_vision

        response = await self._client._request("GET", "/models/names", params=params)
        return response.json()

    def get_model_names_sync(
        self, provider: str, model_type: Optional[str] = None
    ) -> List[str]:
        """Synchronous version of get_model_names."""
        return asyncio.run(self.get_model_names(provider, model_type))

    async def get_providers(self) -> List[str]:
        """
        Get available providers.
        
        Returns:
            List[str]: List of available providers.
        """
        response = await self._client._request("GET", "/models/providers")
        return response.json()

    def get_providers_sync(self) -> List[str]:
        """Synchronous version of get_providers."""
        return asyncio.run(self.get_providers()) 

    async def get_embedding_models(self, provider: Optional[str] = None) -> List[ModelInfo]:
        params = {"provider": provider} if provider else None
        return await self._get("/models/embedding/list", params=params)

    def get_embedding_models_sync(self, provider: Optional[str] = None) -> List[ModelInfo]:
        return asyncio.run(self.get_embedding_models(provider))

    async def get_embedding_model_names(self, provider: Optional[str] = None) -> List[str]:
        params = {"provider": provider} if provider else None
        response = await self._client._request("GET", "/models/embedding/names", params=params)
        return response.json()

    async def get_embedding_providers(self) -> List[str]:
        response = await self._client._request("GET", "/models/embedding/providers")
        return response.json()

    async def get_vision_models(self, provider: Optional[str] = None) -> List[ModelInfo]:
        params = {"provider": provider} if provider else None
        return await self._get("/models/vision", params=params)

    async def list_managed_models(self) -> List[ModelInfo]:
        response = await self._client._request("GET", "/models/manage")
        return [ModelInfo(**item) for item in response.json()]

    async def create_model(self, request: ModelCreateRequest) -> ModelInfo:
        response = await self._client._request(
            "POST", "/models/manage", json_data=request.model_dump(mode="json", exclude_none=True)
        )
        return ModelInfo(**response.json())

    async def get_model(self, model_id: Union[str, UUID]) -> ModelInfo:
        response = await self._client._request("GET", f"/models/manage/{model_id}")
        return ModelInfo(**response.json())

    async def update_model(
        self, model_id: Union[str, UUID], request: ModelUpdateRequest
    ) -> ModelInfo:
        response = await self._client._request(
            "PUT",
            f"/models/manage/{model_id}",
            json_data=request.model_dump(mode="json", exclude_none=True),
        )
        return ModelInfo(**response.json())

    async def delete_model(self, model_id: Union[str, UUID]) -> ModelDeleteResponse:
        response = await self._client._request("DELETE", f"/models/manage/{model_id}")
        return ModelDeleteResponse(**response.json())