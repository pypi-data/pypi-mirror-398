"""
AIRUN SDK Exceptions

Custom exceptions for the AIRUN SDK.
"""

from typing import Optional, Dict, Any


class AIRUNError(Exception):
    """Base exception for all AIRUN SDK errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIError(AIRUNError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.code = code
        self.status_code = status_code


class AuthenticationError(AIRUNError):
    """Raised when authentication fails (invalid API key, etc.)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class ValidationError(AIRUNError):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


class NetworkError(AIRUNError):
    """Raised when network-related errors occur."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class ServerError(APIError):
    """Raised when server encounters an error (5xx)."""

    def __init__(self, message: str = "Server error"):
        super().__init__(message, code="SERVER_ERROR")


class NotFoundError(APIError):
    """Raised when requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND", status_code=404)