"""User controller for Mindzie API.

This controller provides methods for managing users both globally and within tenants.

GLOBAL endpoints (require GLOBAL API key):
- list_users, create_user, get_user, get_user_by_email, update_user, get_user_tenants

TENANT-SCOPED endpoints (accept Global OR Tenant API keys):
- list_tenant_users, create_tenant_user, get_tenant_user, get_tenant_user_by_email,
  update_tenant_user, assign_user_to_tenant, remove_user_from_tenant
"""

from typing import Optional, Dict, Any, List
from urllib.parse import quote
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.models.user import (
    UserListItemDto,
    UserListResponseDto,
    UserCreatedDto,
    UserTenantsResponseDto,
)
from mindzie_api.utils import validate_guid

logger = logging.getLogger(__name__)


class UserController(BaseController):
    """Controller for user-related API endpoints.

    Provides both global user operations (require GLOBAL API key) and
    tenant-scoped operations (accept Global OR Tenant API keys).
    """

    # ========================================
    # GLOBAL ENDPOINTS (Global API Key Required)
    # ========================================

    def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        include_disabled: bool = False,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> UserListResponseDto:
        """Get all users across all tenants with pagination.

        REQUIRES: Global API key

        Args:
            page: Page number (1-based)
            page_size: Number of items per page (max 1000)
            include_disabled: Whether to include disabled users
            role: Filter by role name
            search: Search by email or display name

        Returns:
            UserListResponseDto with paginated list of users

        Raises:
            AuthenticationError: If not using a GLOBAL API key
        """
        params: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "includeDisabled": include_disabled,
        }

        if role:
            params["role"] = role
        if search:
            params["search"] = search

        response = self._request("GET", "api/user", params=params)
        return UserListResponseDto(**response)

    def create_user(
        self,
        email: str,
        display_name: str,
        role_name: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        send_welcome_email: bool = False,
    ) -> UserCreatedDto:
        """Create a new user globally (not assigned to any tenant initially).

        REQUIRES: Global API key

        Args:
            email: User's email address (must be unique)
            display_name: User's display name (2-100 characters)
            role_name: User's role name (e.g., "Administrator", "Analyst", "User")
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            send_welcome_email: Whether to send welcome email (Identity auth only)

        Returns:
            UserCreatedDto with new user details

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            ValidationError: If validation fails (invalid email, etc.)
            ConflictError: If email already exists (DUPLICATE_EMAIL)
        """
        payload: Dict[str, Any] = {
            "email": email,
            "displayName": display_name,
            "roleName": role_name,
            "sendWelcomeEmail": send_welcome_email,
        }

        if first_name:
            payload["firstName"] = first_name
        if last_name:
            payload["lastName"] = last_name

        response = self._request("POST", "api/user", json_data=payload)
        return UserCreatedDto(**response)

    def get_user(self, user_id: str) -> UserListItemDto:
        """Get detailed information for a specific user by ID.

        REQUIRES: Global API key

        Args:
            user_id: The user GUID

        Returns:
            UserListItemDto with full user information including tenant assignments

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If user not found (USER_NOT_FOUND)
            ValueError: If user_id is not a valid GUID
        """
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        response = self._request("GET", f"api/user/{user_id}")
        return UserListItemDto(**response)

    def get_user_by_email(self, email: str) -> UserListItemDto:
        """Get user details by email address.

        REQUIRES: Global API key

        Args:
            email: The user's email address

        Returns:
            UserListItemDto with full user information

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If user not found (USER_NOT_FOUND)
        """
        # URL encode the email address
        encoded_email = quote(email, safe='')
        response = self._request("GET", f"api/user/by-email/{encoded_email}")
        return UserListItemDto(**response)

    def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        role_name: Optional[str] = None,
        disabled: Optional[bool] = None,
        is_service_account: Optional[bool] = None,
        home_tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a user globally (full options).

        REQUIRES: Global API key

        Only provided (non-None) fields will be updated.

        Service Account Rules:
        - Only Administrator and TenantAdmin roles can be service accounts
        - When promoting to service account: home_tenant_id is REQUIRED
        - When demoting: home_tenant_id is automatically cleared

        Args:
            user_id: The user GUID
            display_name: New display name (2-100 characters)
            role_name: New role name
            disabled: Whether to disable the user account
            is_service_account: Whether this is a service account
            home_tenant_id: Home tenant ID (required if is_service_account=True)

        Returns:
            Dict with success message

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If user not found (USER_NOT_FOUND)
            ValidationError: If validation fails (INVALID_ROLE_FOR_SERVICE_ACCOUNT, HOME_TENANT_REQUIRED)
            ValueError: If user_id is not a valid GUID
        """
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        if home_tenant_id and not validate_guid(home_tenant_id):
            raise ValueError(f"Invalid home tenant ID format: {home_tenant_id}")

        payload: Dict[str, Any] = {}

        if display_name is not None:
            payload["displayName"] = display_name
        if role_name is not None:
            payload["roleName"] = role_name
        if disabled is not None:
            payload["disabled"] = disabled
        if is_service_account is not None:
            payload["isServiceAccount"] = is_service_account
        if home_tenant_id is not None:
            payload["homeTenantId"] = home_tenant_id

        return self._request("PUT", f"api/user/{user_id}", json_data=payload)

    def get_user_tenants(self, user_id: str) -> UserTenantsResponseDto:
        """Get all tenant assignments for a user.

        REQUIRES: Global API key

        Args:
            user_id: The user GUID

        Returns:
            UserTenantsResponseDto with list of tenant assignments

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If user not found (USER_NOT_FOUND)
            ValueError: If user_id is not a valid GUID
        """
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        response = self._request("GET", f"api/user/{user_id}/tenants")
        return UserTenantsResponseDto(**response)

    def get_all_users(
        self,
        include_disabled: bool = False,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[UserListItemDto]:
        """Get all users (convenience method with auto-pagination).

        REQUIRES: Global API key

        Args:
            include_disabled: Whether to include disabled users
            role: Filter by role name
            search: Search by email or display name

        Returns:
            List of all users matching the criteria

        Raises:
            AuthenticationError: If not using a GLOBAL API key
        """
        all_users = []
        page = 1
        page_size = 100

        while True:
            response = self.list_users(
                page=page,
                page_size=page_size,
                include_disabled=include_disabled,
                role=role,
                search=search,
            )
            all_users.extend(response.users)

            if not response.has_next:
                break

            page += 1

        return all_users

    # ========================================
    # TENANT-SCOPED ENDPOINTS (Global OR Tenant API Key)
    # ========================================

    def list_tenant_users(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 50,
        include_disabled: bool = False,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> UserListResponseDto:
        """Get users for a specific tenant with pagination.

        ACCEPTS: Global OR Tenant API key

        Args:
            tenant_id: The tenant GUID
            page: Page number (1-based)
            page_size: Number of items per page (max 1000)
            include_disabled: Whether to include disabled users
            role: Filter by role name
            search: Search by email or display name

        Returns:
            UserListResponseDto with paginated list of users

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            ValueError: If tenant_id is not a valid GUID
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")

        params: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "includeDisabled": include_disabled,
        }

        if role:
            params["role"] = role
        if search:
            params["search"] = search

        response = self._request("GET", f"api/tenant/{tenant_id}/user", params=params)
        return UserListResponseDto(**response)

    def create_tenant_user(
        self,
        tenant_id: str,
        email: str,
        display_name: str,
        role_name: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        send_welcome_email: bool = False,
    ) -> UserCreatedDto:
        """Create a user and assign to tenant, or assign existing user to tenant.

        ACCEPTS: Global OR Tenant API key

        If a user with this email already exists, they will be assigned to the tenant.
        Capacity validation is performed against tenant's MaxUserCount and MaxAnalystCount.

        Args:
            tenant_id: The tenant GUID
            email: User's email address
            display_name: User's display name (2-100 characters)
            role_name: User's role name
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            send_welcome_email: Whether to send welcome email (Identity auth only)

        Returns:
            UserCreatedDto with user details and AssignedToTenant flag

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            ValidationError: If validation fails or capacity limits reached
                (USER_LIMIT_REACHED, ANALYST_LIMIT_REACHED)
            ConflictError: If user already assigned to tenant (ALREADY_ASSIGNED)
            ValueError: If tenant_id is not a valid GUID
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")

        payload: Dict[str, Any] = {
            "email": email,
            "displayName": display_name,
            "roleName": role_name,
            "sendWelcomeEmail": send_welcome_email,
        }

        if first_name:
            payload["firstName"] = first_name
        if last_name:
            payload["lastName"] = last_name

        response = self._request("POST", f"api/tenant/{tenant_id}/user", json_data=payload)
        return UserCreatedDto(**response)

    def get_tenant_user(self, tenant_id: str, user_id: str) -> UserListItemDto:
        """Get user details within tenant context.

        ACCEPTS: Global OR Tenant API key

        User must be assigned to the tenant.

        Args:
            tenant_id: The tenant GUID
            user_id: The user GUID

        Returns:
            UserListItemDto with user information

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            NotFoundError: If user not found or not assigned to tenant
                (USER_NOT_FOUND, USER_NOT_IN_TENANT)
            ValueError: If IDs are not valid GUIDs
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        response = self._request("GET", f"api/tenant/{tenant_id}/user/{user_id}")
        return UserListItemDto(**response)

    def get_tenant_user_by_email(self, tenant_id: str, email: str) -> UserListItemDto:
        """Get user by email within tenant context.

        ACCEPTS: Global OR Tenant API key

        User must be assigned to the tenant.

        Args:
            tenant_id: The tenant GUID
            email: The user's email address

        Returns:
            UserListItemDto with user information

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            NotFoundError: If user not found or not assigned to tenant
            ValueError: If tenant_id is not a valid GUID
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")

        encoded_email = quote(email, safe='')
        response = self._request("GET", f"api/tenant/{tenant_id}/user/by-email/{encoded_email}")
        return UserListItemDto(**response)

    def update_tenant_user(
        self,
        tenant_id: str,
        user_id: str,
        display_name: Optional[str] = None,
        role_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update user within tenant (limited scope).

        ACCEPTS: Global OR Tenant API key

        Only display_name and role_name can be updated via tenant-scoped endpoint.
        For full user updates (disabled, isServiceAccount, homeTenantId), use
        the global update_user() method instead.

        Args:
            tenant_id: The tenant GUID
            user_id: The user GUID
            display_name: New display name (2-100 characters)
            role_name: New role name

        Returns:
            Dict with success message

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            NotFoundError: If user not found or not in tenant
            ValidationError: If validation fails
            ValueError: If IDs are not valid GUIDs
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        payload: Dict[str, Any] = {}

        if display_name is not None:
            payload["displayName"] = display_name
        if role_name is not None:
            payload["roleName"] = role_name

        return self._request("PUT", f"api/tenant/{tenant_id}/user/{user_id}", json_data=payload)

    def assign_user_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
        role_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assign an existing user to a tenant.

        ACCEPTS: Global OR Tenant API key

        Capacity validation is performed against tenant's MaxUserCount and MaxAnalystCount.

        Args:
            tenant_id: The tenant GUID
            user_id: The user GUID
            role_name: Optional role override for this tenant assignment

        Returns:
            Dict with success message

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            NotFoundError: If user or tenant not found
            ValidationError: If capacity limits reached (USER_LIMIT_REACHED, ANALYST_LIMIT_REACHED)
            ConflictError: If user already assigned to tenant (ALREADY_ASSIGNED)
            ValueError: If IDs are not valid GUIDs
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        payload: Dict[str, Any] = {}
        if role_name:
            payload["roleName"] = role_name

        return self._request("POST", f"api/tenant/{tenant_id}/user/{user_id}", json_data=payload)

    def remove_user_from_tenant(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from tenant.

        ACCEPTS: Global OR Tenant API key

        This does NOT delete the user from the system - they remain in the system
        and can be assigned to other tenants.

        Args:
            tenant_id: The tenant GUID
            user_id: The user GUID

        Returns:
            Dict with success message

        Raises:
            AuthenticationError: If API key is not valid for this tenant
            NotFoundError: If user not assigned to tenant (NOT_ASSIGNED)
            ValueError: If IDs are not valid GUIDs
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")
        if not validate_guid(user_id):
            raise ValueError(f"Invalid user ID format: {user_id}")

        return self._request("DELETE", f"api/tenant/{tenant_id}/user/{user_id}")
