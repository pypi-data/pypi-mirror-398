"""Custom exceptions for Reminix SDK"""

from typing import Any, Dict, Optional


class ReminixError(Exception):
    """Base exception for all Reminix SDK errors"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.cause = cause


class APIError(ReminixError):
    """Exception raised when an API request fails"""

    def __init__(
        self,
        message: str,
        status: int,
        status_text: str,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status = status
        self.status_text = status_text
        self.response = response


class AuthenticationError(APIError):
    """Exception raised when authentication fails (401/403)"""

    def __init__(
        self,
        message: str = "Authentication failed. Please check your API key.",
        status: int = 401,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status, "Unauthorized", response)


class NetworkError(ReminixError):
    """Exception raised when a network error occurs"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message, cause)
