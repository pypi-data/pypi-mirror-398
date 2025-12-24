"""Enrichment-related models."""

from typing import Optional, List
from pydantic import Field

from mindzie_api.models.base import BaseModel, TimestampedModel, NamedResource


class Enrichment(TimestampedModel, NamedResource):
    """Enrichment model."""
    
    enrichment_id: str = Field(description="Enrichment ID", alias="EnrichmentId")
    project_id: str = Field(description="Project ID", alias="ProjectId")
    dataset_id: Optional[str] = Field(default=None, alias="DatasetId")
    status: str = Field(default="Active", alias="Status")
    notebook_count: int = Field(default=0, alias="NotebookCount")


class EnrichmentListResponse(BaseModel):
    """Response for enrichment list endpoint."""
    
    enrichments: List[Enrichment] = Field(default_factory=list, alias="Enrichments")
    total_count: int = Field(default=0, alias="TotalCount")
    page: int = Field(default=1, alias="Page")
    page_size: int = Field(default=50, alias="PageSize")


class EnrichmentNotebook(BaseModel):
    """Enrichment notebook model."""
    
    notebook_id: str = Field(description="Notebook ID", alias="NotebookId")
    enrichment_id: str = Field(description="Enrichment ID", alias="EnrichmentId")
    name: str = Field(description="Notebook name", alias="Name")
    description: Optional[str] = Field(default=None, alias="Description")
    date_created: str = Field(description="Creation date", alias="DateCreated")
    date_modified: Optional[str] = Field(default=None, alias="DateModified")