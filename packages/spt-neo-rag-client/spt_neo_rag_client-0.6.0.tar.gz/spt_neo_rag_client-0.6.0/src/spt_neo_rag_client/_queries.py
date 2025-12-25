"""Query endpoints for the SPT Neo RAG Client."""

import asyncio
import json
from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, List

from httpx import Response

from .exceptions import NeoRagApiError
from .models import QueryRequest, QueryResponse, QueryStrategyResponse, SourcesResponse

# Type alias for the request function
RequestFunc = Callable[..., Coroutine[Any, Any, Response]]


class QueryEndpoints:
    """Handles query-related API operations."""

    def __init__(self, request_func: RequestFunc, stream_func: Callable[..., Any]):
        self._request = request_func
        self._stream = stream_func

    async def query(self, payload: QueryRequest) -> QueryResponse:
        """Execute a query against a knowledge base."""

        response = await self._request(
            "POST",
            "/queries",
            json_data=payload.model_dump(mode="json", exclude_none=True),
        )
        return QueryResponse(**response.json())

    def query_sync(self, payload: QueryRequest) -> QueryResponse:
        """Synchronous wrapper for :meth:`query`."""

        return asyncio.run(self.query(payload))

    async def stream_query(self, payload: QueryRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a query response from the API."""

        payload.stream = True
        async with self._stream(  # type: ignore[attr-defined]
            "POST",
            "/queries/stream",
            json_data=payload.model_dump(mode="json", exclude_none=True),
        ) as response:
            if response.status_code >= 400:
                error_detail = await response.aread()
                raise NeoRagApiError(
                    status_code=response.status_code,
                    detail=json.loads(error_detail) if error_detail else response.text,
                    headers=dict(response.headers),
                )

            async for line in response.aiter_lines():
                if not line:
                    continue
                yield json.loads(line)

    def stream_query_sync(self, payload: QueryRequest) -> List[Dict[str, Any]]:
        """Sync wrapper around :meth:`stream_query`."""

        async def collect() -> List[Dict[str, Any]]:
            chunks: List[Dict[str, Any]] = []
            async for chunk in self.stream_query(payload):
                chunks.append(chunk)
            return chunks

        return asyncio.run(collect())

    async def get_query_strategies(self) -> QueryStrategyResponse:
        """
        Get available query strategies.
        
        Returns:
            QueryStrategyResponse: List of available strategies.
        """
        response = await self._request("GET", "/queries/strategies")
        return QueryStrategyResponse(**response.json())

    def get_query_strategies_sync(self) -> QueryStrategyResponse:
        """Synchronous version of get_query_strategies."""
        return asyncio.run(self.get_query_strategies())

    async def retrieve_sources(self, payload: QueryRequest) -> SourcesResponse:
        """
        Retrieve relevant sources for a query without generating an answer.

        This is useful for integrations like OpenWebUI where answer generation
        happens client-side. Returns only the relevant source chunks without
        running the LLM for answer generation.

        Args:
            payload: Query request payload

        Returns:
            SourcesResponse: Retrieved sources with metadata
        """
        response = await self._request(
            "POST",
            "/queries/sources",
            json_data=payload.model_dump(mode="json", exclude_none=True),
        )
        return SourcesResponse(**response.json())

    def retrieve_sources_sync(self, payload: QueryRequest) -> SourcesResponse:
        """Synchronous version of retrieve_sources."""
        return asyncio.run(self.retrieve_sources(payload)) 