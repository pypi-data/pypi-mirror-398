"""Dataset-related models."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field

from mindzie_api.models.base import BaseModel, TimestampedModel, NamedResource, PaginatedResponse


class Dataset(TimestampedModel, NamedResource):
    """Dataset model."""
    
    dataset_id: str = Field(description="Dataset unique identifier", alias="DatasetId")
    dataset_name: str = Field(description="Dataset name", alias="DatasetName")
    dataset_description: Optional[str] = Field(default=None, description="Dataset description", alias="DatasetDescription")
    project_id: str = Field(description="Project ID", alias="ProjectId")
    use_date_only_sorting: bool = Field(default=False, alias="UseDateOnlySorting")
    use_only_event_columns: bool = Field(default=False, alias="UseOnlyEventColumns")
    case_id_column_name: Optional[str] = Field(default=None, alias="CaseIdColumnName")
    activity_column_name: Optional[str] = Field(default=None, alias="ActivityColumnName")
    time_column_name: Optional[str] = Field(default=None, alias="TimeColumnName")
    resource_column_name: Optional[str] = Field(default=None, alias="ResourceColumnName")
    begin_time_column_name: Optional[str] = Field(default=None, alias="BeginTimeColumnName")
    expected_order_column_name: Optional[str] = Field(default=None, alias="ExpectedOrderColumnName")
    
    @property
    def name(self) -> str:
        return self.dataset_name
    
    @property
    def description(self) -> Optional[str]:
        return self.dataset_description


class DatasetListResponse(BaseModel):
    """Response for dataset list endpoint."""
    
    items: List[Dataset] = Field(default_factory=list, alias="Items")
    total_count: int = Field(default=0, alias="TotalCount")


class DatasetUploadResponse(BaseModel):
    """Response for dataset upload endpoints."""
    
    dataset_id: str = Field(description="Created dataset ID", alias="DatasetId")
    dataset_name: str = Field(description="Dataset name", alias="DatasetName")
    status: str = Field(description="Upload status", alias="Status")
    message: Optional[str] = Field(default=None, description="Status message", alias="Message")
    row_count: Optional[int] = Field(default=None, description="Number of rows imported", alias="RowCount")
    column_count: Optional[int] = Field(default=None, description="Number of columns", alias="ColumnCount")