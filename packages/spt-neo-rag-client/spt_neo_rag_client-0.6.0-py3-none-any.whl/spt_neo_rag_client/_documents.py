"""Document endpoints for the SPT Neo RAG Client."""

import asyncio
import json
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, List, Optional
from uuid import UUID

from .models import (
    DocumentChunkResponse,
    DocumentPageImageResponse,
    DocumentResponse,
    DocumentUpdate,
)

if TYPE_CHECKING:
    from .client import NeoRagClient


class DocumentEndpoints:
    """Handles document-related API operations."""

    def __init__(self, client: "NeoRagClient"):
        self._client = client

    async def get_processors(self) -> List[str]:
        """
        Get available document processors.
        
        Returns:
            List[str]: List of processor names.
        """
        response = await self._client._request("GET", "/documents/processors")
        return response.json() # Backend returns a simple list

    def get_processors_sync(self) -> List[str]:
        """Synchronous version of get_processors."""
        return asyncio.run(self.get_processors())

    async def get_chunking_strategies(self) -> List[str]:
        """
        Get available chunking strategies.
        
        Returns:
            List[str]: List of strategy names.
        """
        response = await self._client._request("GET", "/documents/chunking-strategies")
        return response.json() # Backend returns a simple list

    def get_chunking_strategies_sync(self) -> List[str]:
        """Synchronous version of get_chunking_strategies."""
        return asyncio.run(self.get_chunking_strategies())

    async def upload_document(
        self,
        file: BinaryIO,
        file_name: str,
        name: str,
        knowledge_base_id: UUID,
        description: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        processor_type: Optional[str] = "langchain",
        processor_config: Optional[Dict[str, Any]] = None,
        credentials: Optional[List[str]] = None,
        force_upload: bool = False,
        extract_structured_content: Optional[bool] = False,
        structured_content_type: Optional[str] = None,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> DocumentResponse:
        """
        Upload a new document to a knowledge base.

        Args:
            file: File object (e.g., opened with 'rb').
            file_name: Original name of the file.
            name: Name for the document in the system.
            knowledge_base_id: ID of the knowledge base.
            description: Optional description.
            source: Optional source information.
            metadata: Optional dictionary of metadata.
            processor_type: Document processor type (default: langchain).
            processor_config: Optional configuration for the processor.
            credentials: Access control credentials.
            force_upload: Force upload even if duplicate detected.
            extract_structured_content: Whether to extract structured content.
            structured_content_type: Type of structured document to extract.
            chunking_strategy: Optional chunking strategy to use (overrides KB default).
            chunk_size: Optional chunk size in characters (overrides KB default).
            chunk_overlap: Optional overlap between chunks (overrides KB default).

        Returns:
            DocumentResponse: Created document details.
        """
        form_data = {
            "name": (None, name),
            "knowledge_base_id": (None, str(knowledge_base_id)),
        }
        if description:
            form_data["description"] = (None, description)
        if source:
            form_data["source"] = (None, source)
        if metadata:
            form_data["metadata"] = (None, json.dumps(metadata))
        if processor_type:
            form_data["processor_type"] = (None, processor_type)
        if processor_config:
            form_data["processor_config"] = (None, json.dumps(processor_config))
        if credentials:
            form_data["credentials"] = (None, json.dumps(credentials))
        else:
             # Ensure default ["ALL"] is sent if None
             form_data["credentials"] = (None, json.dumps(["ALL"]))
        if force_upload:
            form_data["force_upload"] = (None, str(force_upload).lower())
        if extract_structured_content:
            form_data["extract_structured_content"] = (
                None, str(extract_structured_content).lower()
            )
        if structured_content_type:
            if not extract_structured_content:
                raise ValueError(
                    "'structured_content_type' requires 'extract_structured_content'"
                )
            form_data["structured_content_type"] = (None, structured_content_type)
        if chunking_strategy:
            form_data["chunking_strategy"] = (None, chunking_strategy)
        if chunk_size is not None:
            form_data["chunk_size"] = (None, str(chunk_size))
        if chunk_overlap is not None:
            form_data["chunk_overlap"] = (None, str(chunk_overlap))

        # Use generic mime type
        files = {"file": (file_name, file, "application/octet-stream")}

        response = await self._client._request(
            "POST",
            "/documents",
            data=form_data,
            files=files,
        )
        return DocumentResponse(**response.json())

    def upload_document_sync(
        self,
        file: BinaryIO,
        file_name: str,
        name: str,
        knowledge_base_id: UUID,
        description: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        processor_type: Optional[str] = "langchain",
        processor_config: Optional[Dict[str, Any]] = None,
        credentials: Optional[List[str]] = None,
        force_upload: bool = False,
        extract_structured_content: Optional[bool] = False,
        structured_content_type: Optional[str] = None,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> DocumentResponse:
        """Synchronous version of upload_document."""
        return asyncio.run(self.upload_document(
            file=file, file_name=file_name, name=name,
            knowledge_base_id=knowledge_base_id,
            description=description, source=source, metadata=metadata,
            processor_type=processor_type, processor_config=processor_config,
            credentials=credentials, force_upload=force_upload,
            extract_structured_content=extract_structured_content,
            structured_content_type=structured_content_type,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        ))

    async def reprocess_document(self, document_id: UUID) -> DocumentResponse:
        """
        Reprocess a document.

        Args:
            document_id: ID of the document to reprocess.

        Returns:
            DocumentResponse: Document details.
        """
        response = await self._client._request(
            "POST", "/documents/reprocess",
            params={"document_id": str(document_id)}
        )
        return DocumentResponse(**response.json())

    def reprocess_document_sync(self, document_id: UUID) -> DocumentResponse:
        """Synchronous version of reprocess_document."""
        return asyncio.run(self.reprocess_document(document_id))

    async def scrape_web_page(
        self,
        name: str,
        knowledge_base_id: UUID,
        source: str,
        levels: int = 1,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        credentials: Optional[List[str]] = None,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> DocumentResponse:
        """
        Scrape a web page and upload it to a knowledge base.

        Args:
            name: Name for the document in the system.
            knowledge_base_id: ID of the knowledge base.
            source: URL to scrape.
            levels: Number of levels to scrape (1-5).
            description: Optional description.
            metadata: Optional dictionary of metadata.
            credentials: Access control credentials.
            chunking_strategy: Optional chunking strategy to use (overrides KB default).
            chunk_size: Optional chunk size in characters (overrides KB default).
            chunk_overlap: Optional overlap between chunks (overrides KB default).

        Returns:
            DocumentResponse: Created document details.
        """
        form_data = {
            "name": (None, name),
            "knowledge_base_id": (None, str(knowledge_base_id)),
            "source": (None, source),
            "levels": (None, str(levels)),
        }
        if description:
            form_data["description"] = (None, description)
        if metadata:
            form_data["metadata"] = (None, json.dumps(metadata))
        if credentials:
            form_data["credentials"] = (None, json.dumps(credentials))
        else:
             form_data["credentials"] = (None, json.dumps(["ALL"]))
        if chunking_strategy:
            form_data["chunking_strategy"] = (None, chunking_strategy)
        if chunk_size is not None:
            form_data["chunk_size"] = (None, str(chunk_size))
        if chunk_overlap is not None:
            form_data["chunk_overlap"] = (None, str(chunk_overlap))

        response = await self._client._request(
            "POST",
            "/documents/scrape",
            data=form_data,
        )
        return DocumentResponse(**response.json())

    def scrape_web_page_sync(
        self,
        name: str,
        knowledge_base_id: UUID,
        source: str,
        levels: int = 1,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        credentials: Optional[List[str]] = None,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> DocumentResponse:
        """Synchronous version of scrape_web_page."""
        return asyncio.run(self.scrape_web_page(
            name=name, knowledge_base_id=knowledge_base_id,
            source=source, levels=levels, description=description,
            metadata=metadata, credentials=credentials,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        ))

    async def list_documents(
        self,
        knowledge_base_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DocumentResponse]:
        """
        List documents, optionally filtered by knowledge base ID.

        Args:
            knowledge_base_id: Optional ID of the knowledge base to filter by.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            
        Returns:
            List[DocumentResponse]: List of documents.
        """
        params = {"skip": skip, "limit": limit}
        if knowledge_base_id:
            params["knowledge_base_id"] = str(knowledge_base_id)
        
        response = await self._client._request("GET", "/documents/list", params=params)
        return [DocumentResponse(**item) for item in response.json()]

    def list_documents_sync(
        self,
        knowledge_base_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DocumentResponse]:
        """Synchronous version of list_documents."""
        return asyncio.run(self.list_documents(knowledge_base_id, skip, limit))

    async def count_documents(
        self,
        knowledge_base_id: Optional[UUID] = None,
    ) -> int:
        """
        Get the total count of documents, optionally filtered by knowledge base ID.
        
        Args:
            knowledge_base_id: Optional ID of the knowledge base to filter by.
            
        Returns:
            int: Total count of documents.
        """
        params = {}
        if knowledge_base_id:
            params["knowledge_base_id"] = str(knowledge_base_id)
        
        response = await self._client._request("GET", "/documents/count", params=params)
        return response.json()

    def count_documents_sync(
        self,
        knowledge_base_id: Optional[UUID] = None,
    ) -> int:
        """Synchronous version of count_documents."""
        return asyncio.run(self.count_documents(knowledge_base_id))

    async def get_document(self, document_id: UUID) -> DocumentResponse:
        """
        Get a specific document by ID.

        Args:
            document_id: ID of the document.
            
        Returns:
            DocumentResponse: Document details.
        """
        response = await self._client._request("GET", f"/documents/{document_id}")
        return DocumentResponse(**response.json())

    def get_document_sync(self, document_id: UUID) -> DocumentResponse:
        """Synchronous version of get_document."""
        return asyncio.run(self.get_document(document_id))

    async def get_document_download_url(
        self, document_id: UUID, expiration: int = 3600
    ) -> str:
        """
        Get a pre-signed URL to download a document.

        Args:
            document_id: ID of the document.
            expiration: URL expiration time in seconds.

        Returns:
            str: Download URL.
        """
        params = {"expiration": expiration}
        response = await self._client._request(
            "GET", f"/documents/{document_id}/download", params=params
        )
        return response.json()["download_url"]

    def get_document_download_url_sync(
        self, document_id: UUID, expiration: int = 3600
    ) -> str:
        """Synchronous version of get_document_download_url."""
        return asyncio.run(self.get_document_download_url(document_id, expiration))

    async def get_document_content(self, document_id: UUID) -> bytes:
        """
        Get the content of a document.

        Args:
            document_id: ID of the document.
            
        Returns:
            bytes: Raw content of the document.
        """
        response = await self._client._request("GET", f"/documents/{document_id}/content")
        return response.content

    def get_document_content_sync(self, document_id: UUID) -> bytes:
        """Synchronous version of get_document_content."""
        return asyncio.run(self.get_document_content(document_id))

    async def get_document_structured_content(self, document_id: UUID) -> Dict[str, Any]:
        """
        Get the structured content of a document.

        Args:
            document_id: ID of the document.
            
        Returns:
            Dict[str, Any]: Structured content of the document.
        """
        response = await self._client._request(
            "GET", f"/documents/{document_id}/structured_content"
        )
        return response.json()

    def get_document_structured_content_sync(self, document_id: UUID) -> Dict[str, Any]:
        """Synchronous version of get_document_structured_content."""
        return asyncio.run(self.get_document_structured_content(document_id))

    async def update_document(
        self, document_id: UUID, update_data: DocumentUpdate
    ) -> DocumentResponse:
        """
        Update a document.

        Args:
            document_id: ID of the document.
            update_data: Update data.
            
        Returns:
            DocumentResponse: Updated document details.
        """
        response = await self._client._request(
            "PUT",
            f"/documents/{document_id}",
            json_data=update_data.model_dump(mode="json", exclude_unset=True),
        )
        return DocumentResponse(**response.json())

    def update_document_sync(
        self, document_id: UUID, update_data: DocumentUpdate
    ) -> DocumentResponse:
        """Synchronous version of update_document."""
        return asyncio.run(self.update_document(document_id, update_data))

    async def delete_document(self, document_id: UUID) -> Dict[str, Any]:
        """
        Delete a document and all associated data.

        Args:
            document_id: ID of the document.
            
        Returns:
            Dict[str, Any]: Deletion confirmation.
        """
        response = await self._client._request("DELETE", f"/documents/{document_id}")
        return response.status_code == 204

    def delete_document_sync(self, document_id: UUID) -> bool:
        """Synchronous version of delete_document."""
        return asyncio.run(self.delete_document(document_id))

    async def get_document_chunks(
        self, document_id: UUID, skip: int = 0, limit: int = 100, include_embeddings: bool = False
    ) -> List[DocumentChunkResponse]:
        """
        Get chunks for a specific document.

        Args:
            document_id: ID of the document.
            skip: Number of chunks to skip.
            limit: Maximum number of chunks to return.
            include_embeddings: Whether to include embedding vectors.
            
        Returns:
            List[DocumentChunkResponse]: List of document chunks.
        """
        params = {
            "skip": skip, "limit": limit, "include_embeddings": include_embeddings
        }
        response = await self._client._request(
            "GET", f"/documents/{document_id}/chunks", params=params
        )
        return [DocumentChunkResponse(**item) for item in response.json()]

    def get_document_chunks_sync(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_embeddings: bool = False
    ) -> List[DocumentChunkResponse]:
        """Synchronous version of get_document_chunks."""
        return asyncio.run(
            self.get_document_chunks(document_id, skip, limit, include_embeddings)
        )

    async def count_document_chunks(self, document_id: UUID) -> int:
        """
        Get the total count of chunks for a document.

        Args:
            document_id: ID of the document.
            
        Returns:
            int: Total count of chunks.
        """
        response = await self._client._request("GET", f"/documents/{document_id}/chunks/count")
        return response.json()

    def count_document_chunks_sync(self, document_id: UUID) -> int:
        """Synchronous version of count_document_chunks."""
        return asyncio.run(self.count_document_chunks(document_id))

    async def get_document_page_images(
        self, document_id: UUID
    ) -> List[DocumentPageImageResponse]:
        """
        Get page images for a specific document.

        Args:
            document_id: ID of the document.
            
        Returns:
            List[DocumentPageImageResponse]: List of page images.
        """
        response = await self._client._request("GET", f"/documents/{document_id}/page_images")
        return [DocumentPageImageResponse(**item) for item in response.json()]

    def get_document_page_images_sync(
        self, document_id: UUID
    ) -> List[DocumentPageImageResponse]:
        """Synchronous version of get_document_page_images."""
        return asyncio.run(self.get_document_page_images(document_id)) 