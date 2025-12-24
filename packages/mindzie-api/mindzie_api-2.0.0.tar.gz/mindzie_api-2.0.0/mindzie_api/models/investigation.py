"""Investigation-related models."""

from typing import Optional, List
from pydantic import Field

from mindzie_api.models.base import BaseModel, TimestampedModel, NamedResource


class Investigation(TimestampedModel, NamedResource):
    """Investigation model."""
    
    investigation_id: str = Field(description="Investigation ID", alias="InvestigationId")
    project_id: str = Field(description="Project ID", alias="ProjectId")
    investigation_name: str = Field(description="Investigation name", alias="InvestigationName")
    investigation_description: Optional[str] = Field(default=None, alias="InvestigationDescription")
    dataset_id: Optional[str] = Field(default=None, alias="DatasetId")
    investigation_order: int = Field(default=0, alias="InvestigationOrder")
    is_used_for_operation_center: bool = Field(default=False, alias="IsUsedForOperationCenter")
    investigation_folder_id: Optional[str] = Field(default=None, alias="InvestigationFolderId")
    notebook_count: int = Field(default=0, alias="NotebookCount")
    
    @property
    def name(self) -> str:
        return self.investigation_name
    
    @property
    def description(self) -> Optional[str]:
        return self.investigation_description


class InvestigationListResponse(BaseModel):
    """Response for investigation list endpoint."""
    
    investigations: List[Investigation] = Field(default_factory=list, alias="Investigations")
    total_count: int = Field(default=0, alias="TotalCount")
    page: int = Field(default=1, alias="Page")
    page_size: int = Field(default=50, alias="PageSize")