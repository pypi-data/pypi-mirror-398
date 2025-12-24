"""Base models for API responses."""

from typing import Optional, List, TypeVar, Generic, Any, Dict
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model for all API models."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump(exclude_none=True)
    
    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json(exclude_none=True)


T = TypeVar("T", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[T]):
    """Base model for paginated API responses."""
    
    items: List[T] = Field(default_factory=list, description="List of items")
    total_count: int = Field(description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of items per page")
    total_pages: Optional[int] = Field(default=None, description="Total number of pages")
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.total_pages is None and self.page_size > 0:
            self.total_pages = (self.total_count + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < (self.total_pages or 0)
    
    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
    
    @property
    def next_page(self) -> Optional[int]:
        """Get next page number."""
        return self.page + 1 if self.has_next else None
    
    @property
    def previous_page(self) -> Optional[int]:
        """Get previous page number."""
        return self.page - 1 if self.has_previous else None


class TimestampedModel(BaseModel):
    """Base model for resources with timestamps."""
    
    date_created: datetime = Field(description="Creation timestamp")
    date_modified: Optional[datetime] = Field(default=None, description="Last modification timestamp")
    created_by: Optional[str] = Field(default=None, description="User ID who created the resource")
    modified_by: Optional[str] = Field(default=None, description="User ID who last modified the resource")


class NamedResource(BaseModel):
    """Base model for named resources."""
    
    name: str = Field(description="Resource name")
    description: Optional[str] = Field(default=None, description="Resource description")