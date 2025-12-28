"""Custom exception classes for the Outline SDK."""

from typing import Any, Dict, Optional


class OutlineError(Exception):
    """Base exception for all Outline SDK errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize OutlineError.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            data: Additional error data from API response
        """
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(OutlineError):
    """Raised when API authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed. Check your API key.",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, data=data)


class AuthorizationError(OutlineError):
    """Raised when user is not authorized to perform an action (403)."""

    def __init__(
        self,
        message: str = "Not authorized to perform this action.",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=403, data=data)


class NotFoundError(OutlineError):
    """Raised when a requested resource is not found (404)."""

    def __init__(self, message: str = "Resource not found.", data: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, data=data)


class ValidationError(OutlineError):
    """Raised when request validation fails (400)."""

    def __init__(
        self, message: str = "Request validation failed.", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=400, data=data)


class RateLimitError(OutlineError):
    """Raised when API rate limit is exceeded (429)."""

    def __init__(
        self,
        retry_after: int,
        message: str = "Rate limit exceeded.",
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize RateLimitError.

        Args:
            retry_after: Number of seconds to wait before retrying
            message: Error message
            data: Additional error data
        """
        self.retry_after = retry_after
        super().__init__(
            f"{message} Retry after {retry_after} seconds.", status_code=429, data=data
        )


class ServerError(OutlineError):
    """Raised when the server returns a 5xx error."""

    def __init__(
        self,
        message: str = "Server error occurred.",
        status_code: int = 500,
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status_code, data=data)


class NetworkError(OutlineError):
    """Raised when a network-related error occurs."""

    def __init__(
        self, message: str = "Network error occurred.", original_error: Optional[Exception] = None
    ):
        self.original_error = original_error
        if original_error:
            message = f"{message} ({type(original_error).__name__}: {original_error})"
        super().__init__(message)
