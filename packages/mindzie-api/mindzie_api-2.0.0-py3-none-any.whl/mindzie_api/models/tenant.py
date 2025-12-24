"""Tenant-related models."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field

from mindzie_api.models.base import BaseModel


class TenantListItem(BaseModel):
    """Tenant item in list response - matches TenantListItemDto.cs."""

    tenant_id: str = Field(description="Unique identifier for the tenant", alias="tenantId")
    name: str = Field(description="Technical name of the tenant")
    display_name: str = Field(description="Human-friendly display name", alias="displayName")
    description: Optional[str] = Field(default=None, description="Optional description")
    case_count: Optional[int] = Field(default=None, description="Current number of cases", alias="caseCount")
    max_user_count: int = Field(description="Maximum number of users allowed", alias="maxUserCount")
    max_analyst_count: int = Field(description="Maximum number of analysts allowed", alias="maxAnalystCount")
    analyst_count: int = Field(description="Current number of analysts", alias="analystCount")
    user_count: int = Field(description="Current number of users", alias="userCount")
    pre_release: bool = Field(description="Whether pre-release features are enabled", alias="preRelease")
    is_academic: bool = Field(description="Whether this is an academic license tenant", alias="isAcademic")
    autoload: bool = Field(description="Whether tenant should auto-load on user login")
    date_created: datetime = Field(description="When the tenant was created", alias="dateCreated")
    is_disabled: bool = Field(description="Whether the tenant is disabled", alias="isDisabled")
    expiration_date: Optional[datetime] = Field(default=None, description="When the tenant expires (for trial tenants)", alias="expirationDate")
    days_until_expiration: Optional[int] = Field(default=None, description="Days remaining until expiration", alias="daysUntilExpiration")


class TenantListResponse(BaseModel):
    """Paginated response for tenant list - matches TenantListResponseDto.cs."""

    tenants: List[TenantListItem] = Field(default_factory=list, description="List of tenants")
    total_count: int = Field(description="Total count of tenants in the system", alias="totalCount")
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Number of items per page", alias="pageSize")

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size if self.page_size > 0 else 0
        return self.page < total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class TenantDetail(BaseModel):
    """Detailed tenant information - matches TenantDetailDto.cs."""

    tenant_id: str = Field(description="The GUID of the tenant", alias="tenantId")
    name: str = Field(description="Technical name of the tenant")
    display_name: str = Field(description="Human-friendly display name", alias="displayName")
    description: Optional[str] = Field(default=None, description="Tenant description")
    is_academic: bool = Field(description="Academic tenant flag", alias="isAcademic")
    pre_release: bool = Field(description="Pre-release features enabled", alias="preRelease")
    max_user_count: int = Field(description="Maximum number of users", alias="maxUserCount")
    max_analyst_count: int = Field(description="Maximum number of analysts", alias="maxAnalystCount")
    max_cases: Optional[int] = Field(default=None, description="Maximum number of cases (null = unlimited)", alias="maxCases")
    date_created: datetime = Field(description="Date when the tenant was created", alias="dateCreated")
    is_disabled: bool = Field(description="Whether the tenant is disabled", alias="isDisabled")
    expiration_date: Optional[datetime] = Field(default=None, description="When the tenant expires (for trial tenants)", alias="expirationDate")
    days_until_expiration: Optional[int] = Field(default=None, description="Days remaining until expiration", alias="daysUntilExpiration")


class TenantCreated(BaseModel):
    """Response for successful tenant creation - matches TenantCreatedDto.cs."""

    tenant_id: str = Field(description="Unique identifier for the newly created tenant", alias="tenantId")
    name: str = Field(description="Technical name of the tenant")
    display_name: str = Field(description="Display name of the tenant", alias="displayName")
    message: str = Field(description="Success message")
    storage_container_created: bool = Field(description="Whether blob storage container was created", alias="storageContainerCreated")


class TenantUpdated(BaseModel):
    """Response for successful tenant update - matches TenantUpdatedDto.cs."""

    tenant_id: str = Field(description="The GUID of the updated tenant", alias="tenantId")
    name: str = Field(description="Technical name of the tenant")
    display_name: str = Field(description="Display name of the tenant", alias="displayName")
    message: str = Field(description="Success message")
    is_disabled: bool = Field(description="Current disabled status after update", alias="isDisabled")
    expiration_date: Optional[datetime] = Field(default=None, description="Expiration date after update", alias="expirationDate")
