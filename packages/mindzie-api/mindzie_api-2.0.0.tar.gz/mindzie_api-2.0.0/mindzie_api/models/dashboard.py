"""Dashboard-related models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from mindzie_api.models.base import BaseModel, TimestampedModel, NamedResource


class DashboardPanel(BaseModel):
    """Dashboard panel model."""
    
    panel_id: str = Field(description="Panel ID", alias="PanelId")
    name: str = Field(description="Panel name", alias="Name")
    panel_type: str = Field(description="Panel type", alias="PanelType")
    position: int = Field(description="Panel position", alias="Position")
    width: int = Field(description="Panel width", alias="Width")
    height: int = Field(description="Panel height", alias="Height")
    configuration: Optional[Dict[str, Any]] = Field(default=None, alias="Configuration")


class Dashboard(TimestampedModel, NamedResource):
    """Dashboard model."""
    
    dashboard_id: str = Field(description="Dashboard ID", alias="DashboardId")
    project_id: str = Field(description="Project ID", alias="ProjectId")
    panel_count: int = Field(default=0, alias="PanelCount")
    url: Optional[str] = Field(default=None, alias="Url")
    panels: Optional[List[DashboardPanel]] = Field(default=None, alias="Panels")


class DashboardListResponse(BaseModel):
    """Response for dashboard list endpoint."""
    
    dashboards: List[Dashboard] = Field(default_factory=list, alias="Dashboards")
    total_count: int = Field(default=0, alias="TotalCount")
    page: int = Field(default=1, alias="Page")
    page_size: int = Field(default=50, alias="PageSize")