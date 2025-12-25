"""User endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import UUID

from .models import (
    UserCreate,
    UserResponse,
    UserUpdate,
)

# Type alias for the request function
RequestFunc = Callable[..., Coroutine[Any, Any, Any]]


class UserEndpoints:
    """Handles user-related API operations (requires admin usually)."""

    def __init__(self, request_func: RequestFunc):
        self._request = request_func

    # Note: /users/me is implicitly covered by /auth/me in this client's structure
    # async def get_current_user_details(self) -> UserResponse:
    #     """ Get details for the currently authenticated user. """
    #     response = await self._request("GET", "/users/me")
    #     return UserResponse(**response.json())

    # def get_current_user_details_sync(self) -> UserResponse:
    #     """ Synchronous version of get_current_user_details. """
    #     return asyncio.run(self.get_current_user_details())

    async def update_current_user(self, update_data: UserUpdate) -> UserResponse:
        """
        Update details for the currently authenticated user.

        Args:
            update_data: UserUpdate model with fields to change.
            
        Returns:
            UserResponse: Updated user details.
        """
        response = await self._request(
            "PATCH", "/users/me", json_data=update_data.model_dump(mode="json", exclude_unset=True)
        )
        return UserResponse(**response.json())

    def update_current_user_sync(self, update_data: UserUpdate) -> UserResponse:
        """Synchronous version of update_current_user."""
        return asyncio.run(self.update_current_user(update_data))

    async def list_users(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[UserResponse]:
        """
        List users (admin only).

        Args:
            skip: Number of users to skip.
            limit: Maximum number of users to return.
            is_active: Filter by active status.
            
        Returns:
            List[UserResponse]: List of users.
        """
        params = {"skip": skip, "limit": limit}
        if is_active is not None:
            params["is_active"] = is_active
        response = await self._request("GET", "/users/", params=params)
        return [UserResponse(**item) for item in response.json()]

    def list_users_sync(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[UserResponse]:
        """Synchronous version of list_users."""
        return asyncio.run(self.list_users(skip, limit, is_active))

    async def create_user(self, create_data: UserCreate) -> UserResponse:
        """
        Create a new user (admin only).

        Args:
            create_data: UserCreate model with user details.
            
        Returns:
            UserResponse: Created user details.
        """
        response = await self._request("POST", "/users/", json_data=create_data.model_dump(mode="json"))
        return UserResponse(**response.json())

    def create_user_sync(self, create_data: UserCreate) -> UserResponse:
        """Synchronous version of create_user."""
        return asyncio.run(self.create_user(create_data))

    async def get_user(self, user_id: UUID) -> UserResponse:
        """
        Get details for a specific user by ID (admin only).

        Args:
            user_id: ID of the user.
            
        Returns:
            UserResponse: User details.
        """
        response = await self._request("GET", f"/users/{user_id}")
        return UserResponse(**response.json())

    def get_user_sync(self, user_id: UUID) -> UserResponse:
        """Synchronous version of get_user."""
        return asyncio.run(self.get_user(user_id))

    async def update_user(
        self, user_id: UUID, update_data: UserUpdate
    ) -> UserResponse:
        """
        Update details for a specific user by ID (admin only).

        Args:
            user_id: ID of the user to update.
            update_data: UserUpdate model with fields to change.
            
        Returns:
            UserResponse: Updated user details.
        """
        response = await self._request(
            "PUT", f"/users/{user_id}", json_data=update_data.model_dump(mode="json", exclude_unset=True)
        )
        return UserResponse(**response.json())

    def update_user_sync(
        self, user_id: UUID, update_data: UserUpdate
    ) -> UserResponse:
        """Synchronous version of update_user."""
        return asyncio.run(self.update_user(user_id, update_data))

    async def delete_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Delete a specific user by ID (admin only).

        Args:
            user_id: ID of the user to delete.
            
        Returns:
            Dict[str, Any]: Confirmation message.
        """
        response = await self._request("DELETE", f"/users/{user_id}")
        return response.json() # Returns {"message": "User deleted successfully"}

    def delete_user_sync(self, user_id: UUID) -> Dict[str, Any]:
        """Synchronous version of delete_user."""
        return asyncio.run(self.delete_user(user_id)) 