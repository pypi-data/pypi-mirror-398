from typing import Any, Dict
from uuid import uuid4

import pytest

from spt_neo_rag_client.client import NeoRagClient
from spt_neo_rag_client.models import QueryRequest, QueryResponse


class StubbedClient(NeoRagClient):
    def __init__(self) -> None:
        super().__init__(base_url="https://api.test", api_key="test-key")
        self.requests: Dict[str, Any] = {}

    async def _request(self, method: str, path: str, **kwargs):
        self.requests[path] = {
            "method": method,
            "headers": self._prepare_headers(kwargs.get("headers")),
            "json": kwargs.get("json_data"),
        }
        class Response:
            def json(self_inner):
                return {
                    "result": {
                        "query": "hello",
                        "answer": "world",
                        "sources": [],
                    },
                    "knowledge_base_id": str(uuid4()),
                    "knowledge_base_ids": [str(uuid4()), str(uuid4())],
                    "processing_time_ms": 1.0,
                    "token_usage": {},
                }
        return Response()

    def _stream_request(self, method: str, path: str, **kwargs):  # type: ignore
        raise NotImplementedError


@pytest.mark.asyncio
async def test_litellm_header_is_forwarded():
    client = StubbedClient()
    client.set_litellm_api_key("tenant-key")

    payload = QueryRequest(
        knowledge_base_ids=[uuid4(), uuid4()],
        query="hello",
    )

    response = await client.queries.query(payload)

    assert isinstance(response, QueryResponse)
    request_meta = client.requests["/queries"]
    assert request_meta["headers"]["LiteLLM-API-Key"] == "tenant-key"
    assert request_meta["headers"]["X-API-Key"] == "test-key"
    assert request_meta["json"]["knowledge_base_ids"]

    await client.close()
