"""Execution-related models."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field

from mindzie_api.models.base import BaseModel


class ExecutionQueueItem(BaseModel):
    """Execution queue item model."""
    
    execution_id: str = Field(description="Execution ID", alias="ExecutionId")
    project_id: str = Field(description="Project ID", alias="ProjectId")
    resource_type: str = Field(description="Resource type", alias="ResourceType")
    resource_id: str = Field(description="Resource ID", alias="ResourceId")
    resource_name: Optional[str] = Field(default=None, alias="ResourceName")
    status: str = Field(description="Execution status", alias="Status")
    priority: int = Field(default=0, alias="Priority")
    queued_time: datetime = Field(description="Queue time", alias="QueuedTime")
    start_time: Optional[datetime] = Field(default=None, alias="StartTime")
    estimated_duration_ms: Optional[int] = Field(default=None, alias="EstimatedDurationMs")


class ExecutionHistory(BaseModel):
    """Execution history item model."""
    
    execution_id: str = Field(description="Execution ID", alias="ExecutionId")
    project_id: str = Field(description="Project ID", alias="ProjectId")
    resource_type: str = Field(description="Resource type", alias="ResourceType")
    resource_id: str = Field(description="Resource ID", alias="ResourceId")
    resource_name: Optional[str] = Field(default=None, alias="ResourceName")
    status: str = Field(description="Execution status", alias="Status")
    start_time: datetime = Field(description="Start time", alias="StartTime")
    end_time: Optional[datetime] = Field(default=None, alias="EndTime")
    duration_ms: Optional[int] = Field(default=None, alias="DurationMs")
    error_message: Optional[str] = Field(default=None, alias="ErrorMessage")
    created_by: Optional[str] = Field(default=None, alias="CreatedBy")


class ExecutionStatus(BaseModel):
    """Execution status model."""
    
    execution_id: str = Field(description="Execution ID", alias="ExecutionId")
    status: str = Field(description="Current status", alias="Status")
    progress_percentage: Optional[int] = Field(default=None, alias="ProgressPercentage")
    current_step: Optional[str] = Field(default=None, alias="CurrentStep")
    total_steps: Optional[int] = Field(default=None, alias="TotalSteps")
    start_time: Optional[datetime] = Field(default=None, alias="StartTime")
    estimated_completion: Optional[datetime] = Field(default=None, alias="EstimatedCompletion")
    messages: Optional[List[str]] = Field(default=None, alias="Messages")