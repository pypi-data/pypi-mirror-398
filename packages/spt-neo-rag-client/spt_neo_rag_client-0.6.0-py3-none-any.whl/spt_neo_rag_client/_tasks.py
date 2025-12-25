"""Task endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import UUID

from .models import (
    TaskResponse,
)

# Type alias for the request function
RequestFunc = Callable[..., Coroutine[Any, Any, Any]]


class TaskEndpoints:
    """Handles task-related API operations."""

    def __init__(self, request_func: RequestFunc):
        self._request = request_func

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        include_completed: bool = False,
        completed_limit: int = 50,
        status: Optional[List[str]] = None,
        queue: Optional[List[str]] = None,
        worker: Optional[List[str]] = None,
        document_id: Optional[UUID] = None,
        knowledge_base_id: Optional[UUID] = None,
    ) -> List[TaskResponse]:
        """
        Get all tasks with optional filtering and pagination.

        Args:
            skip: Number of tasks to skip (default: 0).
            limit: Maximum number of tasks to return (default: 100).
            include_completed: Include recently completed tasks (default: False).
            completed_limit: Maximum number of completed tasks to include (default: 50).
            status: Filter by task status (e.g., ["pending", "running"]).
            queue: Filter by queue name.
            worker: Filter by worker name.
            document_id: Filter by document ID.
            knowledge_base_id: Filter by knowledge base ID.

        Returns:
            List[TaskResponse]: List of tasks matching the criteria.
        """
        params: Dict[str, Any] = {
            "skip": skip,
            "limit": limit,
            "include_completed": include_completed,
            "completed_limit": completed_limit,
        }
        if status:
            params["status"] = status
        if queue:
            params["queue"] = queue
        if worker:
            params["worker"] = worker
        if document_id:
            params["document_id"] = str(document_id)
        if knowledge_base_id:
            params["knowledge_base_id"] = str(knowledge_base_id)

        response = await self._request("GET", "/tasks", params=params)
        return [TaskResponse(**item) for item in response.json()]

    def list_tasks_sync(
        self,
        skip: int = 0,
        limit: int = 100,
        include_completed: bool = False,
        completed_limit: int = 50,
        status: Optional[List[str]] = None,
        queue: Optional[List[str]] = None,
        worker: Optional[List[str]] = None,
        document_id: Optional[UUID] = None,
        knowledge_base_id: Optional[UUID] = None,
    ) -> List[TaskResponse]:
        """Synchronous version of list_tasks."""
        return asyncio.run(self.list_tasks(
            skip=skip,
            limit=limit,
            include_completed=include_completed,
            completed_limit=completed_limit,
            status=status,
            queue=queue,
            worker=worker,
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
        ))

    async def get_task(self, task_id: UUID) -> TaskResponse:
        """
        Get details for a specific task.

        Args:
            task_id: ID of the task.
            
        Returns:
            TaskResponse: Task details.
        """
        response = await self._request("GET", f"/tasks/{task_id}")
        return TaskResponse(**response.json())

    def get_task_sync(self, task_id: UUID) -> TaskResponse:
        """Synchronous version of get_task."""
        return asyncio.run(self.get_task(task_id))

    async def delete_task(self, task_id: UUID) -> Dict[str, Any]:
        """
        Cancel a running task (sends delete request).

        Args:
            task_id: ID of the task to cancel.
            
        Returns:
            Dict[str, Any]: Confirmation message (or None on 204).
        """
        response = await self._request("DELETE", f"/tasks/{task_id}")
        # Returns 204 No Content on success
        if response.status_code == 204:
            return {"status": "success", "message": f"Task {task_id} cancellation requested."}
        return response.json() # Should ideally not happen on success

    def delete_task_sync(self, task_id: UUID) -> Dict[str, Any]:
        """Synchronous version of delete_task."""
        return asyncio.run(self.delete_task(task_id))

    async def get_document_tasks(self, document_id: UUID) -> List[TaskResponse]:
        """
        Get all tasks related to a specific document.

        Args:
            document_id: ID of the document.
            
        Returns:
            List[TaskResponse]: List of tasks for the document.
        """
        response = await self._request("GET", f"/tasks/document/{document_id}")
        return [TaskResponse(**item) for item in response.json()]

    def get_document_tasks_sync(self, document_id: UUID) -> List[TaskResponse]:
        """Synchronous version of get_document_tasks."""
        return asyncio.run(self.get_document_tasks(document_id))

    async def get_knowledge_base_tasks(self, knowledge_base_id: UUID) -> List[TaskResponse]:
        """
        Get all tasks related to a specific knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base.

        Returns:
            List[TaskResponse]: List of tasks for the knowledge base.
        """
        response = await self._request("GET", f"/tasks/knowledge-base/{knowledge_base_id}")
        return [TaskResponse(**item) for item in response.json()]

    def get_knowledge_base_tasks_sync(self, knowledge_base_id: UUID) -> List[TaskResponse]:
        """Synchronous version of get_knowledge_base_tasks."""
        return asyncio.run(self.get_knowledge_base_tasks(knowledge_base_id)) 