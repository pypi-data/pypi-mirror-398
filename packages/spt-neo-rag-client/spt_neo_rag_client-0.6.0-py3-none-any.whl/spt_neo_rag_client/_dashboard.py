"""
Dashboard endpoints for the SPT Neo RAG Client.

This module provides methods for accessing dashboard metrics and analytics.
"""

from typing import Any, Callable, Dict


class DashboardEndpoints:
    """Endpoints for dashboard metrics and analytics."""

    def __init__(self, request_func: Callable):
        """
        Initialize Dashboard endpoints.

        Args:
            request_func: The client's _request method for making API calls
        """
        self._request = request_func

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get dashboard metrics for the platform.

        Returns comprehensive metrics including:
        - Database statistics (table sizes, row counts)
        - Neo4j graph statistics
        - Document statistics by status
        - Chunk statistics
        - Knowledge base statistics
        - Recent errors

        Requires admin/superuser permissions.

        Returns:
            Dict[str, Any]: Dashboard metrics
        """
        response = await self._request("GET", "/dashboard/metrics")
        return response.json()

    async def get_analytics(self, period: str = "30d") -> Dict[str, Any]:
        """
        Get time-series analytics for the dashboard.

        Args:
            period: Time period for analytics. Options: "7d", "30d", "90d", "1y"

        Returns comprehensive analytics including:
        - Documents created over time
        - Knowledge bases over time
        - Failed ingestions over time
        - Processing success rate
        - Chunks generated over time
        - Current stats with period changes
        - Ingestion time by MIME type
        - Ingestion time evolution

        Requires admin/superuser permissions.

        Returns:
            Dict[str, Any]: Analytics data
        """
        params = {"period": period}
        response = await self._request("GET", "/dashboard/analytics", params=params)
        return response.json()

    async def get_documents_by_mime_type(
        self, mime_type: str, period: str = "30d", limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get documents by MIME type with ingestion time details.

        Args:
            mime_type: MIME type to filter documents (e.g., "application/pdf")
            period: Time period for filtering. Options: "7d", "30d", "90d", "1y"
            limit: Maximum number of documents to return (1-200)

        Requires admin/superuser permissions.

        Returns:
            Dict[str, Any]: Documents filtered by MIME type
        """
        params = {"mime_type": mime_type, "period": period, "limit": limit}
        response = await self._request(
            "GET", "/dashboard/documents-by-mime", params=params
        )
        return response.json()
