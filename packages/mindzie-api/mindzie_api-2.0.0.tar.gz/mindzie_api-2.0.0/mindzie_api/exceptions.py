"""Custom exceptions for the Mindzie API client."""

from typing import Optional, Dict, Any


class MindzieAPIException(Exception):
    """Base exception for all Mindzie API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        self.request_id = request_id
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status Code: {self.status_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return " | ".join(parts)


class AuthenticationError(MindzieAPIException):
    """Raised when authentication fails."""
    pass


class ValidationError(MindzieAPIException):
    """Raised when request validation fails."""
    pass


class NotFoundError(MindzieAPIException):
    """Raised when a requested resource is not found."""
    pass


class ServerError(MindzieAPIException):
    """Raised when the server returns a 5xx error."""
    pass


class RateLimitError(MindzieAPIException):
    """Raised when API rate limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class TimeoutError(MindzieAPIException):
    """Raised when a request times out."""
    pass


class ConnectionError(MindzieAPIException):
    """Raised when connection to the API fails."""
    pass


class ConflictError(MindzieAPIException):
    """Raised when a resource conflict occurs (HTTP 409).

    This typically happens with optimistic locking when the resource
    has been modified by another user since it was last retrieved.
    """

    def __init__(
        self,
        message: str,
        date_modified: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.date_modified = date_modified

    def __str__(self) -> str:
        base = super().__str__()
        if self.date_modified:
            return f"{base} | Server DateModified: {self.date_modified}"
        return base