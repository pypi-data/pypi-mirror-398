"""
Settings endpoints for the SPT Neo RAG Client.

This module provides methods for accessing public and system settings.
"""

from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from .models import PublicSettings


class SettingsEndpoints:
    """Endpoints for public settings."""

    def __init__(self, request_func: Callable):
        """
        Initialize Settings endpoints.

        Args:
            request_func: The client's _request method for making API calls
        """
        self._request = request_func

    async def get_public_settings(self) -> PublicSettings:
        """
        Get public-facing settings.

        Returns publicly accessible settings like:
        - enable_user_registration

        No authentication required.

        Returns:
            PublicSettings: Public settings
        """
        response = await self._request("GET", "/settings/public")
        return PublicSettings(**response.json())


class SystemSettingsEndpoints:
    """Endpoints for system settings (admin only)."""

    def __init__(self, request_func: Callable):
        """
        Initialize System Settings endpoints.

        Args:
            request_func: The client's _request method for making API calls
        """
        self._request = request_func

    async def get_settings(self) -> Dict[str, Any]:
        """
        Get system settings.

        Returns current system configuration settings with masked API keys.
        Requires admin/superuser permissions.

        Returns:
            Dict[str, Any]: System settings (API keys are masked)
        """
        response = await self._request("GET", "/admin/settings")
        return response.json()

    async def update_settings(self, settings_update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update system settings.

        API keys are automatically encrypted before storage.
        Masked values (containing asterisks) are ignored.
        Set a field to null to reset it to the environment variable default.

        Requires admin/superuser permissions.

        Args:
            settings_update: Settings to update

        Returns:
            Dict[str, Any]: Updated system settings (API keys are masked)
        """
        response = await self._request(
            "PUT", "/admin/settings", json_data=settings_update
        )
        return response.json()

    async def reset_setting(self, setting_key: str) -> Dict[str, Any]:
        """
        Reset a specific setting to its default value.

        Sets the database value to null, causing the system to fall back
        to the environment variable value.

        Requires admin/superuser permissions.

        Args:
            setting_key: Key of the setting to reset

        Returns:
            Dict[str, Any]: Reset confirmation
        """
        response = await self._request("DELETE", f"/admin/settings/{setting_key}")
        return response.json()

    async def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the settings cache.

        Forces the system to reload settings from the database on the next request.
        Requires admin/superuser permissions.

        Returns:
            Dict[str, Any]: Cache clear confirmation
        """
        response = await self._request("POST", "/admin/settings/clear-cache")
        return response.json()

    # Configuration CRUD endpoints

    async def create_configuration(
        self, scope: str, key: str, config: Dict[str, Any], description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new configuration entry.

        Requires admin/superuser permissions.

        Args:
            scope: Configuration scope (e.g., "loader", "chunking")
            key: Configuration key
            config: Configuration data (JSON)
            description: Optional description

        Returns:
            Dict[str, Any]: Created configuration
        """
        config_data = {
            "scope": scope,
            "key": key,
            "config": config,
        }
        if description:
            config_data["description"] = description

        response = await self._request(
            "POST", "/admin/settings/configurations", json_data=config_data
        )
        return response.json()

    async def list_configurations(
        self,
        scope: Optional[str] = None,
        active_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all configurations with optional filtering.

        Requires admin/superuser permissions.

        Args:
            scope: Optional scope filter
            active_only: Only return active configurations
            limit: Maximum number of results (1-1000)
            offset: Number of results to skip

        Returns:
            List[Dict[str, Any]]: List of configurations
        """
        params = {"active_only": active_only, "offset": offset}
        if scope:
            params["scope"] = scope
        if limit:
            params["limit"] = limit

        response = await self._request(
            "GET", "/admin/settings/configurations", params=params
        )
        return response.json()

    async def get_configuration(self, config_id: UUID) -> Dict[str, Any]:
        """
        Get a specific configuration by ID.

        Requires admin/superuser permissions.

        Args:
            config_id: Configuration ID

        Returns:
            Dict[str, Any]: Configuration details
        """
        response = await self._request(
            "GET", f"/admin/settings/configurations/{config_id}"
        )
        return response.json()

    async def get_configurations_by_scope(
        self, scope: str, active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all configurations for a specific scope.

        Requires admin/superuser permissions.

        Args:
            scope: Configuration scope
            active_only: Only return active configurations

        Returns:
            List[Dict[str, Any]]: List of configurations for the scope
        """
        params = {"active_only": active_only}
        response = await self._request(
            "GET", f"/admin/settings/configurations/scope/{scope}", params=params
        )
        return response.json()

    async def get_configuration_by_scope_key(
        self, scope: str, key: str
    ) -> Dict[str, Any]:
        """
        Get a specific configuration by scope and key.

        Requires admin/superuser permissions.

        Args:
            scope: Configuration scope
            key: Configuration key

        Returns:
            Dict[str, Any]: Configuration details
        """
        response = await self._request(
            "GET", f"/admin/settings/configurations/scope/{scope}/key/{key}"
        )
        return response.json()

    async def update_configuration(
        self, config_id: UUID, config_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a configuration entry.

        All fields in the update request are optional.
        Requires admin/superuser permissions.

        Args:
            config_id: Configuration ID
            config_update: Fields to update

        Returns:
            Dict[str, Any]: Updated configuration
        """
        response = await self._request(
            "PUT",
            f"/admin/settings/configurations/{config_id}",
            json_data=config_update,
        )
        return response.json()

    async def delete_configuration(self, config_id: UUID) -> Dict[str, Any]:
        """
        Delete a configuration entry.

        Requires admin/superuser permissions.

        Args:
            config_id: Configuration ID

        Returns:
            Dict[str, Any]: Deletion confirmation
        """
        response = await self._request(
            "DELETE", f"/admin/settings/configurations/{config_id}"
        )
        return response.json()
