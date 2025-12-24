"""Copilot-related models."""

from typing import Optional, List
from pydantic import Field

from mindzie_api.models.base import BaseModel


class RunCopilotNotebookTemplateRequest(BaseModel):
    """Request model for running copilot notebook template."""
    
    project_id: str = Field(description="Project ID", alias="ProjectId")
    dataset_id: str = Field(description="Dataset ID", alias="DatasetId")
    investigation_id: Optional[str] = Field(default=None, description="Investigation ID", alias="InvestigationId")
    notebook_template_id: Optional[str] = Field(default=None, description="Notebook template ID", alias="NotebookTemplateId")
    output_type: Optional[str] = Field(default=None, description="Output type", alias="OutputType")
    prompt: Optional[str] = Field(default=None, description="Copilot prompt", alias="Prompt")


class RunCopilotNotebookRequest(BaseModel):
    """Request model for running copilot notebook."""
    
    project_id: str = Field(description="Project ID", alias="ProjectId")
    dataset_id: str = Field(description="Dataset ID", alias="DatasetId")
    notebook_id: str = Field(description="Notebook ID", alias="NotebookId")
    investigation_id: Optional[str] = Field(default=None, description="Investigation ID", alias="InvestigationId")
    output_type: Optional[str] = Field(default=None, description="Output type", alias="OutputType")
    prompt: Optional[str] = Field(default=None, description="Copilot prompt", alias="Prompt")


class CopilotNotebookResult(BaseModel):
    """Result model for copilot notebook execution."""
    
    output_text: str = Field(description="Output text", alias="OutputText")
    success: bool = Field(description="Success status", alias="Success")
    error_message: Optional[str] = Field(default=None, description="Error message", alias="ErrorMessage")
    execution_id: Optional[str] = Field(default=None, description="Execution ID", alias="ExecutionId")
    notebook_id: Optional[str] = Field(default=None, description="Created notebook ID", alias="NotebookId")


class AvailableCopilotOutput(BaseModel):
    """Model for available copilot output."""
    
    output_id: str = Field(description="Output ID", alias="OutputId")
    output_name: str = Field(description="Output name", alias="OutputName")
    output_type: str = Field(description="Output type", alias="OutputType")
    dataset_id: str = Field(description="Dataset ID", alias="DatasetId")
    investigation_id: Optional[str] = Field(default=None, description="Investigation ID", alias="InvestigationId")
    notebook_id: Optional[str] = Field(default=None, description="Notebook ID", alias="NotebookId")
    created_date: str = Field(description="Creation date", alias="CreatedDate")
    created_by: Optional[str] = Field(default=None, description="Created by user", alias="CreatedBy")