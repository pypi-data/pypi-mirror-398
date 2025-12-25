"""Team endpoints for the SPT Neo RAG Client."""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List
from uuid import UUID

from .models import (
    GenericStatusResponse,
    KnowledgeBaseResponseMinimal,
    TeamCreate,
    TeamDetailResponse,
    TeamResponse,
    TeamUpdate,
    UserResponseMinimal,
)

# Type alias for the request function
RequestFunc = Callable[..., Coroutine[Any, Any, Any]]


class TeamEndpoints:
    """Handles team, membership, and sharing-related API operations."""

    def __init__(self, request_func: RequestFunc):
        self._request = request_func

    # --- Team CRUD ---

    async def create_team(self, create_data: TeamCreate) -> TeamResponse:
        """
        Create a new team. The authenticated user becomes the owner.

        Args:
            create_data: TeamCreate model with team details.
            
        Returns:
            TeamResponse: Created team details.
        """
        response = await self._request("POST", "/teams/", json_data=create_data.model_dump(mode="json"))
        return TeamResponse(**response.json())

    def create_team_sync(self, create_data: TeamCreate) -> TeamResponse:
        """Synchronous version of create_team."""
        return asyncio.run(self.create_team(create_data))

    async def list_teams(self, skip: int = 0, limit: int = 100) -> List[TeamResponse]:
        """
        List teams.

        Args:
            skip: Number of teams to skip.
            limit: Maximum number of teams to return.
            
        Returns:
            List[TeamResponse]: List of teams.
        """
        params = {"skip": skip, "limit": limit}
        response = await self._request("GET", "/teams/", params=params)
        return [TeamResponse(**item) for item in response.json()]

    def list_teams_sync(self, skip: int = 0, limit: int = 100) -> List[TeamResponse]:
        """Synchronous version of list_teams."""
        return asyncio.run(self.list_teams(skip, limit))

    async def get_team(self, team_id: UUID) -> TeamDetailResponse:
        """
        Get details for a specific team, including members and shared KBs.

        Args:
            team_id: ID of the team.
            
        Returns:
            TeamDetailResponse: Detailed team information.
        """
        response = await self._request("GET", f"/teams/{team_id}")
        return TeamDetailResponse(**response.json())

    def get_team_sync(self, team_id: UUID) -> TeamDetailResponse:
        """Synchronous version of get_team."""
        return asyncio.run(self.get_team(team_id))

    async def update_team(self, team_id: UUID, update_data: TeamUpdate) -> TeamResponse:
        """
        Update team details (name, description). Only the owner can.

        Args:
            team_id: ID of the team to update.
            update_data: TeamUpdate model with fields to change.
            
        Returns:
            TeamResponse: Updated team details.
        """
        response = await self._request(
            "PUT", f"/teams/{team_id}", json_data=update_data.model_dump(mode="json", exclude_unset=True)
        )
        return TeamResponse(**response.json())

    def update_team_sync(self, team_id: UUID, update_data: TeamUpdate) -> TeamResponse:
        """Synchronous version of update_team."""
        return asyncio.run(self.update_team(team_id, update_data))

    async def delete_team(self, team_id: UUID) -> Dict[str, Any]:
        """
        Delete a team. Only the owner can.

        Args:
            team_id: ID of the team to delete.
            
        Returns:
            Dict[str, Any]: Confirmation message (or None on 204).
        """
        response = await self._request("DELETE", f"/teams/{team_id}")
        # Returns 204 No Content on success
        if response.status_code == 204:
            return {"status": "success", "message": f"Team {team_id} deleted."}
        return response.json()

    def delete_team_sync(self, team_id: UUID) -> Dict[str, Any]:
        """Synchronous version of delete_team."""
        return asyncio.run(self.delete_team(team_id))

    # --- Team Membership ---

    async def add_user_to_team(
        self, team_id: UUID, user_id_to_add: UUID
    ) -> TeamResponse:
        """
        Add a user to a team. Requires team ownership.

        Args:
            team_id: ID of the team.
            user_id_to_add: ID of the user to add.
            
        Returns:
            TeamResponse: Updated team details (might not change, confirm API behavior).
        """
        response = await self._request("POST", f"/teams/{team_id}/users/{user_id_to_add}")
        return TeamResponse(**response.json())

    def add_user_to_team_sync(
        self, team_id: UUID, user_id_to_add: UUID
    ) -> TeamResponse:
        """Synchronous version of add_user_to_team."""
        return asyncio.run(self.add_user_to_team(team_id, user_id_to_add))

    async def remove_user_from_team(
        self, team_id: UUID, user_id_to_remove: UUID
    ) -> TeamResponse:
        """
        Remove a user from a team. Owner can remove anyone; users can remove themselves.

        Args:
            team_id: ID of the team.
            user_id_to_remove: ID of the user to remove.
            
        Returns:
            TeamResponse: Updated team details (might not change, confirm API behavior).
        """
        response = await self._request("DELETE", f"/teams/{team_id}/users/{user_id_to_remove}")
        return TeamResponse(**response.json())

    def remove_user_from_team_sync(
        self, team_id: UUID, user_id_to_remove: UUID
    ) -> TeamResponse:
        """Synchronous version of remove_user_from_team."""
        return asyncio.run(self.remove_user_from_team(team_id, user_id_to_remove))

    async def list_team_members(
        self, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[UserResponseMinimal]:
        """
        List members of a specific team.

        Args:
            team_id: ID of the team.
            skip: Number of members to skip.
            limit: Maximum number of members to return.
            
        Returns:
            List[UserResponseMinimal]: List of team members.
        """
        params = {"skip": skip, "limit": limit}
        response = await self._request("GET", f"/teams/{team_id}/users/", params=params)
        return [UserResponseMinimal(**item) for item in response.json()]

    def list_team_members_sync(
        self, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[UserResponseMinimal]:
        """Synchronous version of list_team_members."""
        return asyncio.run(self.list_team_members(team_id, skip, limit))

    # --- Knowledge Base Sharing ---

    async def share_kb_with_team(
        self, team_id: UUID, kb_id: UUID
    ) -> GenericStatusResponse:
        """
        Share a knowledge base with a team. Requires team ownership or KB ownership (TBD by API).

        Args:
            team_id: ID of the team.
            kb_id: ID of the knowledge base to share.
            
        Returns:
            GenericStatusResponse: Confirmation message.
        """
        response = await self._request("POST", f"/teams/{team_id}/knowledgebases/{kb_id}")
        return GenericStatusResponse(**response.json())

    def share_kb_with_team_sync(
        self, team_id: UUID, kb_id: UUID
    ) -> GenericStatusResponse:
        """Synchronous version of share_kb_with_team."""
        return asyncio.run(self.share_kb_with_team(team_id, kb_id))

    async def unshare_kb_from_team(
        self, team_id: UUID, kb_id: UUID
    ) -> GenericStatusResponse:
        """
        Unshare a knowledge base from a team. Requires team ownership or KB ownership (TBD by API).

        Args:
            team_id: ID of the team.
            kb_id: ID of the knowledge base to unshare.
            
        Returns:
            GenericStatusResponse: Confirmation message.
        """
        response = await self._request("DELETE", f"/teams/{team_id}/knowledgebases/{kb_id}")
        return GenericStatusResponse(**response.json())

    def unshare_kb_from_team_sync(
        self, team_id: UUID, kb_id: UUID
    ) -> GenericStatusResponse:
        """Synchronous version of unshare_kb_from_team."""
        return asyncio.run(self.unshare_kb_from_team(team_id, kb_id))

    async def list_shared_kbs_for_team(
        self, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[KnowledgeBaseResponseMinimal]:
        """
        List knowledge bases shared with a specific team.

        Args:
            team_id: ID of the team.
            skip: Number of KBs to skip.
            limit: Maximum number of KBs to return.
            
        Returns:
            List[KnowledgeBaseResponseMinimal]: List of shared KBs.
        """
        params = {"skip": skip, "limit": limit}
        response = await self._request("GET", f"/teams/{team_id}/knowledgebases/", params=params)
        return [KnowledgeBaseResponseMinimal(**item) for item in response.json()]

    def list_shared_kbs_for_team_sync(
        self, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[KnowledgeBaseResponseMinimal]:
        """Synchronous version of list_shared_kbs_for_team."""
        return asyncio.run(self.list_shared_kbs_for_team(team_id, skip, limit)) 