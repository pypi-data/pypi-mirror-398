"""
Exceptions for the SPT Neo RAG Client.

This module contains custom exceptions that can be raised by the client.
"""

from typing import Any, Dict, Optional


class NeoRagException(Exception):
    """Base exception for all SPT Neo RAG client exceptions."""
    pass


class NeoRagApiError(NeoRagException):
    """Exception raised when the API returns an error response."""
    
    def __init__(
        self, 
        status_code: int, 
        detail: Any, 
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        
        if isinstance(detail, dict) and "message" in detail:
            message = detail["message"]
        elif isinstance(detail, str):
            message = detail
        else:
            message = str(detail)
            
        super().__init__(f"API Error ({status_code}): {message}")


class AuthenticationError(NeoRagException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(message)


class ConfigurationError(NeoRagException):
    """Exception raised when the client is not configured properly."""
    
    def __init__(self, message: str = "Client configuration error"):
        self.message = message
        super().__init__(message)


class NetworkError(NeoRagException):
    """Exception raised when a network error occurs."""

    def __init__(
        self,
        message: str = "Network error",
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.original_error = original_error
        err_msg = f"{message}: {original_error}" if original_error else message
        super().__init__(err_msg)
