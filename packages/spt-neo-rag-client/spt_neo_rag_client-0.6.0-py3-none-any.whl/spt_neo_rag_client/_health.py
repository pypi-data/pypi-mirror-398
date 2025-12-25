"""Health check endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import TYPE_CHECKING, Any, Dict

from .models import (
    DetailedHealthCheckResponse,
    HealthCheckResponse,
)

if TYPE_CHECKING:
    from .client import NeoRagClient


class HealthEndpoints:
    """Handles health check API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def get_health(self) -> HealthCheckResponse:
        """
        Perform a simple health check.
        
        Returns:
            HealthCheckResponse: Basic status information.
        """
        # Note: Needs authentication header even for basic health
        response = await self._client._request("GET", "/health")
        return HealthCheckResponse(**response.json())

    def get_health_sync(self) -> HealthCheckResponse:
        """Synchronous version of get_health."""
        return asyncio.run(self.get_health())

    async def get_detailed_health(self) -> DetailedHealthCheckResponse:
        """
        Perform a detailed health check including database connection.
        
        Returns:
            DetailedHealthCheckResponse: Detailed status of components.
        """
        response = await self._client._request("GET", "/health/detailed")
        return DetailedHealthCheckResponse(**response.json())

    def get_detailed_health_sync(self) -> DetailedHealthCheckResponse:
        """Synchronous version of get_detailed_health."""
        return asyncio.run(self.get_detailed_health())

    async def get_version(self) -> Dict[str, Any]:
        """
        Get the application version.
        
        Returns:
            Dict[str, Any]: Version information.
        """
        response = await self._client._request("GET", "/health/version")
        return response.json()

    def get_version_sync(self) -> Dict[str, Any]:
        """Synchronous version of get_version."""
        return asyncio.run(self.get_version())

    async def database_health(self) -> Dict[str, Any]:
        """
        Perform a database-specific health check.
        
        Returns:
            Dict[str, Any]: Database health information.
        """
        response = await self._client._request("GET", "/health/database")
        return response.json()

    def database_health_sync(self) -> Dict[str, Any]:
        """Synchronous version of database_health."""
        return asyncio.run(self.database_health())

    async def pool_health(self) -> Dict[str, Any]:
        """
        Perform a database connection pool health check.
        
        Returns:
            Dict[str, Any]: Pool health information.
        """
        response = await self._client._request("GET", "/health/pool")
        return response.json()

    def pool_health_sync(self) -> Dict[str, Any]:
        """Synchronous version of pool_health."""
        return asyncio.run(self.pool_health())