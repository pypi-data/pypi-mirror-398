"""Project-related models."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field

from mindzie_api.models.base import BaseModel, PaginatedResponse


class Project(BaseModel):
    """Project model matching actual API response structure."""
    
    project_id: str = Field(description="Project unique identifier", alias="ProjectId")
    tenant_id: str = Field(description="Tenant unique identifier", alias="TenantId")
    project_name: str = Field(description="Project name", alias="ProjectName")
    project_description: Optional[str] = Field(default=None, description="Project description", alias="ProjectDescription")
    date_created: datetime = Field(description="Creation timestamp", alias="DateCreated")
    date_modified: Optional[datetime] = Field(default=None, description="Last modification timestamp", alias="DateModified")
    created_by: Optional[str] = Field(default=None, description="User ID who created the resource", alias="CreatedBy")
    modified_by: Optional[str] = Field(default=None, description="User ID who last modified the resource", alias="ModifiedBy")
    is_active: bool = Field(default=True, description="Whether project is active", alias="IsActive")
    dataset_count: int = Field(default=0, description="Number of datasets", alias="DatasetCount")
    investigation_count: int = Field(default=0, description="Number of investigations", alias="InvestigationCount")
    dashboard_count: int = Field(default=0, description="Number of dashboards", alias="DashboardCount")
    user_count: int = Field(default=0, description="Number of users", alias="UserCount")
    
    # Convenience properties for backward compatibility
    @property
    def name(self) -> str:
        return self.project_name
    
    @property
    def description(self) -> Optional[str]:
        return self.project_description


class ProjectListResponse(BaseModel):
    """Response for project list endpoint matching actual API structure."""
    
    projects: List[Project] = Field(default_factory=list, description="List of projects", alias="Projects")
    total_count: int = Field(description="Total number of projects", alias="TotalCount")
    page: int = Field(default=1, description="Current page number", alias="Page")
    page_size: int = Field(default=50, description="Number of items per page", alias="PageSize")
    
    @property
    def items(self) -> List[Project]:
        return self.projects
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        return self.page < total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class ProjectSummaryStatistics(BaseModel):
    """Project summary statistics nested model."""
    
    total_datasets: int = Field(default=0, description="Total datasets", alias="TotalDatasets")
    total_investigations: int = Field(default=0, description="Total investigations", alias="TotalInvestigations")
    total_dashboards: int = Field(default=0, description="Total dashboards", alias="TotalDashboards")
    total_notebooks: int = Field(default=0, description="Total notebooks", alias="TotalNotebooks")
    total_users: int = Field(default=0, description="Total users", alias="TotalUsers")


class ProjectSummary(BaseModel):
    """Project summary model matching actual API response structure."""
    
    project_id: str = Field(description="Project unique identifier", alias="ProjectId")
    project_name: str = Field(description="Project name", alias="ProjectName")
    project_description: Optional[str] = Field(default=None, description="Project description", alias="ProjectDescription")
    date_created: datetime = Field(description="Creation timestamp", alias="DateCreated")
    date_modified: Optional[datetime] = Field(default=None, description="Last modification timestamp", alias="DateModified")
    statistics: ProjectSummaryStatistics = Field(description="Summary statistics", alias="Statistics")