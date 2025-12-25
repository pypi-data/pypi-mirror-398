"""Admin endpoints for the SPT Neo RAG Client."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from .models import (
    LicenseStatusResponse,
    MaintenanceResponse,
    TokenUsageResponse,
)

if TYPE_CHECKING:
    from .client import NeoRagClient


class AdminEndpoints:
    """Handles admin-related API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def get_token_usage(
        self,
        period: str = "day",
        model: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> TokenUsageResponse:
        """
        Get token usage statistics (admin only).
        
        Args:
            period: Period to aggregate by (day, week, month, year).
            model: Filter by specific model.
            start_date: Start date for custom range.
            end_date: End date for custom range.
            
        Returns:
            TokenUsageResponse: Token usage data.
        """
        params = {"period": period}
        if model:
            params["model"] = model
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        response = await self._client._request(
            "GET", "/admin/token-usage", params=params
        )
        return TokenUsageResponse(**response.json())

    def get_token_usage_sync(
        self,
        period: str = "day",
        model: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> TokenUsageResponse:
        """Synchronous version of get_token_usage."""
        return asyncio.run(self.get_token_usage(period, model, start_date, end_date))

    async def optimize_vector_indexes(self) -> MaintenanceResponse:
        """
        Trigger background task to optimize vector indexes (admin only).
        
        Returns:
            MaintenanceResponse: Task status information.
        """
        response = await self._client._request(
            "POST", "/admin/maintenance/optimize-vectors"
        )
        return MaintenanceResponse(**response.json())

    def optimize_vector_indexes_sync(self) -> MaintenanceResponse:
        """Synchronous version of optimize_vector_indexes."""
        return asyncio.run(self.optimize_vector_indexes())

    async def collect_statistics(self) -> MaintenanceResponse:
        """
        Trigger background task to collect system usage statistics (admin only).
        
        Returns:
            MaintenanceResponse: Task status information.
        """
        response = await self._client._request(
            "POST", "/admin/maintenance/collect-stats"
        )
        return MaintenanceResponse(**response.json())

    def collect_statistics_sync(self) -> MaintenanceResponse:
        """Synchronous version of collect_statistics."""
        return asyncio.run(self.collect_statistics())



    async def get_license_status(self) -> LicenseStatusResponse:
        """
        Get the current license status information (admin only).
        
        Returns:
            LicenseStatusResponse: License details.
        """
        response = await self._client._request("GET", "/admin/license")
        return LicenseStatusResponse(**response.json())

    def get_license_status_sync(self) -> LicenseStatusResponse:
        """Synchronous version of get_license_status."""
        return asyncio.run(self.get_license_status())



    # System Monitoring Endpoints
    async def get_rate_limit_stats(self) -> Dict[str, Any]:
        """
        Get current rate limiting statistics (admin only).
        
        Returns:
            Dict[str, Any]: Rate limiting statistics.
        """
        response = await self._client._request("GET", "/admin/rate-limit-stats")
        return response.json()

    def get_rate_limit_stats_sync(self) -> Dict[str, Any]:
        """Synchronous version of get_rate_limit_stats."""
        return asyncio.run(self.get_rate_limit_stats())

    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system metrics (admin only).
        
        Returns:
            Dict[str, Any]: System metrics data.
        """
        response = await self._client._request("GET", "/admin/system-metrics")
        return response.json()

    def get_system_metrics_sync(self) -> Dict[str, Any]:
        """Synchronous version of get_system_metrics."""
        return asyncio.run(self.get_system_metrics())

    async def clear_rate_limit_cache(self) -> Dict[str, Any]:
        """
        Clear rate limiting cache for debugging (admin only).
        
        Returns:
            Dict[str, Any]: Cache clearing result.
        """
        response = await self._client._request("POST", "/admin/clear-rate-limit-cache")
        return response.json()

    def clear_rate_limit_cache_sync(self) -> Dict[str, Any]:
        """Synchronous version of clear_rate_limit_cache."""
        return asyncio.run(self.clear_rate_limit_cache())


