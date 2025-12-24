"""User-related models for Mindzie API."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field

from mindzie_api.models.base import BaseModel


class TenantAssignmentDto(BaseModel):
    """Represents a tenant assignment for a user - matches TenantAssignmentDto.cs."""

    tenant_id: str = Field(description="The tenant ID", alias="tenantId")
    tenant_name: str = Field(description="The technical name of the tenant", alias="tenantName")
    tenant_display_name: str = Field(description="The display name of the tenant", alias="tenantDisplayName")
    role_name: Optional[str] = Field(default=None, description="User's role in this tenant", alias="roleName")
    assigned_date: datetime = Field(description="Date the user was assigned to this tenant", alias="assignedDate")


class UserListItemDto(BaseModel):
    """Represents a user in a list view - matches UserListItemDto.cs."""

    user_id: str = Field(description="The unique identifier for the user", alias="userId")
    email: str = Field(description="User's email address (unique)")
    display_name: str = Field(description="User's display name", alias="displayName")
    first_name: Optional[str] = Field(default=None, description="User's first name", alias="firstName")
    last_name: Optional[str] = Field(default=None, description="User's last name", alias="lastName")
    role_name: str = Field(description="User's role name", alias="roleName")
    disabled: bool = Field(description="Whether the user account is disabled")
    is_service_account: bool = Field(description="Whether this is a service account", alias="isServiceAccount")
    home_tenant_id: Optional[str] = Field(default=None, description="Home tenant ID for service accounts", alias="homeTenantId")
    home_tenant_name: Optional[str] = Field(default=None, description="Home tenant name for service accounts", alias="homeTenantName")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp", alias="lastLogin")
    tenant_count: int = Field(description="Number of tenants this user is assigned to", alias="tenantCount")
    tenant_names: Optional[str] = Field(default=None, description="Comma-separated list of tenant names", alias="tenantNames")
    tenants: Optional[List[TenantAssignmentDto]] = Field(default=None, description="Detailed tenant assignments")
    date_created: datetime = Field(description="Date the user account was created", alias="dateCreated")


class UserListResponseDto(BaseModel):
    """Paginated response for user list - matches UserListResponseDto.cs."""

    users: List[UserListItemDto] = Field(default_factory=list, description="List of users")
    total_count: int = Field(description="Total number of users matching the query", alias="totalCount")
    page: int = Field(description="Current page number")
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


class UserCreatedDto(BaseModel):
    """Response for successful user creation - matches UserCreatedDto.cs."""

    user_id: str = Field(description="The ID of the created user", alias="userId")
    email: str = Field(description="User's email address")
    display_name: str = Field(description="User's display name", alias="displayName")
    message: str = Field(description="Success message")
    assigned_to_tenant: bool = Field(description="Whether the user was assigned to a tenant during creation", alias="assignedToTenant")
    tenant_id: Optional[str] = Field(default=None, description="The tenant ID if assigned", alias="tenantId")
    welcome_email_sent: bool = Field(description="Whether a welcome email was sent", alias="welcomeEmailSent")


class UserTenantsResponseDto(BaseModel):
    """Response containing all tenant assignments for a user - matches UserTenantsResponseDto.cs."""

    user_id: str = Field(description="The user's unique identifier", alias="userId")
    email: str = Field(description="The user's email address")
    display_name: str = Field(description="The user's display name", alias="displayName")
    tenants: List[TenantAssignmentDto] = Field(default_factory=list, description="List of all tenants the user is assigned to")

    @property
    def tenant_count(self) -> int:
        """Get total number of tenant assignments."""
        return len(self.tenants) if self.tenants else 0
