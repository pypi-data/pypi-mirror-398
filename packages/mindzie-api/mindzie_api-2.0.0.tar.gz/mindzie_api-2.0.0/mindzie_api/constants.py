"""Constants and enums for the Mindzie API client."""

from enum import Enum


class BlockType(Enum):
    """Block types supported by the API."""
    FILTER = "filter"
    CALCULATOR = "calculator"
    ALERT = "alert"
    ENRICHMENT = "enrichment"
    DASHBOARD = "dashboard"
    PYTHON = "python"
    SQL = "sql"
    MULESOFT = "mulesoft"
    EMAIL = "email"
    COPILOT = "copilot"


class ExecutionStatus(Enum):
    """Execution status values."""
    PENDING = "Pending"
    QUEUED = "Queued"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    TIMEOUT = "Timeout"


class PanelType(Enum):
    """Dashboard panel types."""
    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    TEXT = "text"
    IMAGE = "image"


class DatasetType(Enum):
    """Dataset upload types."""
    CSV = "csv"
    PACKAGE = "package"
    BINARY = "binary"


class AuthType(Enum):
    """Authentication types."""
    API_KEY = "api_key"
    BEARER = "bearer"
    AZURE_AD = "azure_ad"


# API Configuration
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1  # seconds
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_RATE_LIMIT = 429
HTTP_SERVER_ERROR = 500
HTTP_GATEWAY_TIMEOUT = 504