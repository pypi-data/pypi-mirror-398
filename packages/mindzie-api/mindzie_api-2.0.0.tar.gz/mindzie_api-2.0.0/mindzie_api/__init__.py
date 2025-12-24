"""
Mindzie API Python Client Library

A comprehensive Python client for interacting with the Mindzie Studio API.
Provides complete coverage of all API endpoints with type-safe responses,
automatic retries, and comprehensive error handling.
"""

from mindzie_api.__version__ import __version__, __author__, __email__, __license__
from mindzie_api.client import MindzieAPIClient
from mindzie_api.exceptions import (
    MindzieAPIException,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ServerError,
    RateLimitError,
    TimeoutError,
    ConflictError
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "MindzieAPIClient",
    "MindzieAPIException",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "RateLimitError",
    "TimeoutError",
    "ConflictError"
]