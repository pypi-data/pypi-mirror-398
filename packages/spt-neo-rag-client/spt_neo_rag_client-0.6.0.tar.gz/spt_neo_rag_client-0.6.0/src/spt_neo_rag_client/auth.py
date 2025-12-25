"""
Authentication handling for the SPT Neo RAG Client.

This module handles token-based and API key authentication.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from httpx import AsyncClient

from .exceptions import AuthenticationError, NeoRagApiError
from .models import Token


class Auth:
    """
    Handles authentication for the SPT Neo RAG Client.

    Supports:
    - API key authentication
    - Token-based authentication (username/password)
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the Auth handler.

        Args:
            base_url: Base URL of the API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.token: Optional[Token] = None
        self._client = AsyncClient(base_url=f"{self.base_url}/api/v1")

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
        
    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        if self.api_key:
            return True
            
        if self.token:
            # Check if token is still valid
            now = datetime.now(timezone.utc)
            if self.token.expires_at > now:
                return True
                
        return False
        
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Dict with appropriate authentication headers
        """
        headers = {
            "Accept": "application/json",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.token:
            headers["Authorization"] = f"{self.token.token_type} {self.token.access_token}"
            
        return headers
        
    async def login(self, username: str, password: str) -> Token:
        """
        Authenticate with username and password.
        
        Args:
            username: User's email
            password: User's password
            
        Returns:
            Token: Authentication token
            
        Raises:
            AuthenticationError: If authentication fails
        """
        data = {
            "username": username,
            "password": password,
        }
        
        try:
            response = await self._client.post(
                "auth/login",
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.token = Token(**token_data)
            return self.token
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid username or password") from e

            error_detail = e.response.json() if e.response.text else str(e)
            raise NeoRagApiError(
                status_code=e.response.status_code,
                detail=error_detail,
                headers=dict(e.response.headers),
            ) from e

        except httpx.RequestError as e:
            raise AuthenticationError(f"Login request failed: {e}") from e

    async def logout(self) -> bool:
        """
        Logout the current user.
        
        Returns:
            bool: True if logout was successful
            
        Raises:
            AuthenticationError: If not authenticated
        """
        if not self.is_authenticated:
            raise AuthenticationError("Not authenticated")
            
        if self.api_key:
            # API key authentication doesn't have logout
            return True
            
        try:
            response = await self._client.post(
                "auth/logout",
                headers=self.get_headers(),
            )
            response.raise_for_status()
            
            # Clear the token
            self.token = None
            return True
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else str(e)
            raise NeoRagApiError(
                status_code=e.response.status_code,
                detail=error_detail,
                headers=dict(e.response.headers),
            ) from e

        except httpx.RequestError as e:
            raise AuthenticationError(f"Logout request failed: {e}") from e

    def set_api_key(self, api_key: str):
        """
        Set the API key for authentication.
        
        Args:
            api_key: API key
        """
        self.api_key = api_key
        self.token = None  # Clear any existing token

    async def change_password(self, current_password: str, new_password: str) -> bool:
        """
        Change the current user's password.

        Args:
            current_password: The user's current password.
            new_password: The new password.

        Returns:
            True if the password was changed successfully.
        """
        if not self.is_authenticated or not self.token:
            raise AuthenticationError("Must be logged in with username/password to change password.")

        try:
            response = await self._client.post(
                "auth/change-password",
                headers=self.get_headers(),
                json={"current_password": current_password, "new_password": new_password},
            )
            response.raise_for_status()
            return response.json().get("message") == "Password changed successfully"
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else str(e)
            raise NeoRagApiError(
                status_code=e.response.status_code,
                detail=error_detail,
                headers=dict(e.response.headers),
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(f"Password change request failed: {e}") from e

    async def register(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            email: The new user's email.
            password: The new user's password.
            name: The new user's name.

        Returns:
            A dictionary containing the new user's information.
        """
        try:
            response = await self._client.post(
                "auth/register",
                json={"email": email, "password": password, "name": name},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else str(e)
            raise NeoRagApiError(
                status_code=e.response.status_code,
                detail=error_detail,
                headers=dict(e.response.headers),
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(f"Registration request failed: {e}") from e

    async def request_password_reset(self, email: str) -> Dict[str, str]:
        """
        Request a password reset for a user.

        Args:
            email: The email of the user requesting the reset.

        Returns:
            A dictionary with a status message.
        """
        try:
            response = await self._client.post(
                "auth/password-reset",
                json={"email": email},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else str(e)
            raise NeoRagApiError(
                status_code=e.response.status_code,
                detail=error_detail,
                headers=dict(e.response.headers),
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(f"Password reset request failed: {e}") from e
