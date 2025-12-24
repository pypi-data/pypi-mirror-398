"""Data models for Mindzie API responses."""

from mindzie_api.models.base import BaseModel, PaginatedResponse
from mindzie_api.models.project import Project, ProjectListResponse, ProjectSummary
from mindzie_api.models.dataset import Dataset, DatasetListResponse, DatasetUploadResponse
from mindzie_api.models.investigation import Investigation, InvestigationListResponse
from mindzie_api.models.notebook import Notebook, NotebookListResponse, NotebookBlock, NotebookExecutionStatus
from mindzie_api.models.block import Block, BlockListResponse, BlockExecutionResult, BlockOutput
from mindzie_api.models.execution import ExecutionQueueItem, ExecutionHistory, ExecutionStatus
from mindzie_api.models.enrichment import Enrichment, EnrichmentListResponse, EnrichmentNotebook
from mindzie_api.models.dashboard import Dashboard, DashboardListResponse, DashboardPanel
from mindzie_api.models.copilot import (
    RunCopilotNotebookTemplateRequest,
    RunCopilotNotebookRequest,
    CopilotNotebookResult,
    AvailableCopilotOutput
)
from mindzie_api.models.tenant import (
    TenantListItem,
    TenantListResponse,
    TenantDetail,
    TenantCreated,
    TenantUpdated
)
from mindzie_api.models.user import (
    TenantAssignmentDto,
    UserListItemDto,
    UserListResponseDto,
    UserCreatedDto,
    UserTenantsResponseDto
)

__all__ = [
    # Base
    "BaseModel",
    "PaginatedResponse",

    # Project
    "Project",
    "ProjectListResponse",
    "ProjectSummary",

    # Dataset
    "Dataset",
    "DatasetListResponse",
    "DatasetUploadResponse",

    # Investigation
    "Investigation",
    "InvestigationListResponse",

    # Notebook
    "Notebook",
    "NotebookListResponse",
    "NotebookBlock",
    "NotebookExecutionStatus",

    # Block
    "Block",
    "BlockListResponse",
    "BlockExecutionResult",
    "BlockOutput",

    # Execution
    "ExecutionQueueItem",
    "ExecutionHistory",
    "ExecutionStatus",

    # Enrichment
    "Enrichment",
    "EnrichmentListResponse",
    "EnrichmentNotebook",

    # Dashboard
    "Dashboard",
    "DashboardListResponse",
    "DashboardPanel",

    # Tenant
    "TenantListItem",
    "TenantListResponse",
    "TenantDetail",
    "TenantCreated",
    "TenantUpdated",

    # User
    "TenantAssignmentDto",
    "UserListItemDto",
    "UserListResponseDto",
    "UserCreatedDto",
    "UserTenantsResponseDto",
]