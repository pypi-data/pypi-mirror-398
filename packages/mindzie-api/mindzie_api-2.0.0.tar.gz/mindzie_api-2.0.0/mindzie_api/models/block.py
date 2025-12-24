"""Block-related models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from mindzie_api.models.base import BaseModel, TimestampedModel


class Block(TimestampedModel):
    """Block model."""
    
    block_id: str = Field(description="Block ID", alias="BlockId")
    notebook_id: str = Field(description="Notebook ID", alias="NotebookId")
    block_name: str = Field(description="Block name", alias="BlockName")
    block_type: str = Field(description="Block type", alias="BlockType")
    block_order: int = Field(description="Block order", alias="BlockOrder")
    configuration: Optional[Dict[str, Any]] = Field(default=None, alias="Configuration")
    last_execution_time: Optional[str] = Field(default=None, alias="LastExecutionTime")
    last_execution_status: Optional[str] = Field(default=None, alias="LastExecutionStatus")


class BlockListResponse(BaseModel):
    """Response for block list endpoint."""
    
    blocks: List[Block] = Field(default_factory=list, alias="Blocks")
    total_count: int = Field(default=0, alias="TotalCount")


class BlockExecutionResult(BaseModel):
    """Block execution result model."""
    
    block_id: str = Field(description="Block ID", alias="BlockId")
    execution_id: str = Field(description="Execution ID", alias="ExecutionId")
    status: str = Field(description="Execution status", alias="Status")
    start_time: Optional[str] = Field(default=None, alias="StartTime")
    end_time: Optional[str] = Field(default=None, alias="EndTime")
    duration_ms: Optional[int] = Field(default=None, alias="DurationMs")
    row_count: Optional[int] = Field(default=None, alias="RowCount")
    error_message: Optional[str] = Field(default=None, alias="ErrorMessage")


class BlockOutput(BaseModel):
    """Block output data model."""
    
    block_id: str = Field(description="Block ID", alias="BlockId")
    output_type: str = Field(description="Output type", alias="OutputType")
    data: Optional[Any] = Field(default=None, alias="Data")
    row_count: Optional[int] = Field(default=None, alias="RowCount")
    column_count: Optional[int] = Field(default=None, alias="ColumnCount")
    columns: Optional[List[str]] = Field(default=None, alias="Columns")