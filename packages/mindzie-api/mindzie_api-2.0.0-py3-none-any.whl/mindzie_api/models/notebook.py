"""Notebook-related models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from mindzie_api.models.base import BaseModel, TimestampedModel, NamedResource


class NotebookBlock(BaseModel):
    """Notebook block model."""
    
    block_id: str = Field(description="Block ID", alias="BlockId")
    notebook_id: str = Field(description="Notebook ID", alias="NotebookId")
    block_name: str = Field(description="Block name", alias="BlockName")
    block_type: str = Field(description="Block type", alias="BlockType")
    block_order: int = Field(description="Block order", alias="BlockOrder")
    configuration: Optional[Dict[str, Any]] = Field(default=None, alias="Configuration")


class Notebook(TimestampedModel, NamedResource):
    """Notebook model."""
    
    notebook_id: str = Field(description="Notebook ID", alias="NotebookId")
    investigation_id: str = Field(description="Investigation ID", alias="InvestigationId")
    notebook_name: str = Field(description="Notebook name", alias="NotebookName")
    notebook_description: Optional[str] = Field(default=None, alias="NotebookDescription")
    is_main_notebook: bool = Field(default=False, alias="IsMainNotebook")
    block_count: int = Field(default=0, alias="BlockCount")
    blocks: Optional[List[NotebookBlock]] = Field(default=None, alias="Blocks")
    
    @property
    def name(self) -> str:
        return self.notebook_name
    
    @property
    def description(self) -> Optional[str]:
        return self.notebook_description


class NotebookListResponse(BaseModel):
    """Response for notebook list endpoint."""
    
    notebooks: List[Notebook] = Field(default_factory=list, alias="Notebooks")
    total_count: int = Field(default=0, alias="TotalCount")


class NotebookExecutionStatus(BaseModel):
    """Notebook execution status model."""
    
    notebook_id: str = Field(description="Notebook ID", alias="NotebookId")
    execution_id: Optional[str] = Field(default=None, alias="ExecutionId")
    status: str = Field(description="Execution status", alias="Status")
    start_time: Optional[str] = Field(default=None, alias="StartTime")
    end_time: Optional[str] = Field(default=None, alias="EndTime")
    duration_ms: Optional[int] = Field(default=None, alias="DurationMs")
    blocks_completed: int = Field(default=0, alias="BlocksCompleted")
    blocks_total: int = Field(default=0, alias="BlocksTotal")
    error_message: Optional[str] = Field(default=None, alias="ErrorMessage")