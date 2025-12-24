"""Tenant controller for Mindzie API.

IMPORTANT: All tenant operations require a GLOBAL API key, not a tenant-specific key.
Global API keys can be created at /admin/global-api-keys in the mindzieStudio UI.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.models.tenant import (
    TenantListItem,
    TenantListResponse,
    TenantDetail,
    TenantCreated,
    TenantUpdated,
)
from mindzie_api.utils import validate_guid, clean_dict

logger = logging.getLogger(__name__)


class TenantController(BaseController):
    """Controller for tenant-related API endpoints.

    NOTE: All methods in this controller require a GLOBAL API key.
    Tenant-specific API keys will result in 401 Unauthorized errors.
    """

    def ping(self) -> str:
        """Test API connectivity (unauthenticated).

        Returns:
            Ping response message
        """
        response = self._request("GET", "api/ping/unauthorizedping")
        return response if isinstance(response, str) else response.get("data", "pong")

    def list_tenants(self, page: int = 1, page_size: int = 50) -> TenantListResponse:
        """Get all tenants with pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page (max 100)

        Returns:
            TenantListResponse with list of tenants

        Raises:
            AuthenticationError: If not using a GLOBAL API key
        """
        params = {"page": page, "pageSize": page_size}
        response = self._request("GET", "api/tenant", params=params)
        return TenantListResponse(**response)

    def get_tenant(self, tenant_id: str) -> TenantDetail:
        """Get detailed information about a specific tenant.

        Args:
            tenant_id: The tenant GUID

        Returns:
            TenantDetail with full tenant information

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If tenant not found
            ValueError: If tenant_id is not a valid GUID
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")

        response = self._request("GET", f"api/tenant/{tenant_id}")
        return TenantDetail(**response)

    def create_tenant(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        timezone: Optional[str] = None,
        max_users: int = 1,
        max_analyst: int = 1,
        max_cases: Optional[int] = None,
        expiration_date: Optional[Union[datetime, str]] = None,
    ) -> TenantCreated:
        """Create a new tenant.

        Args:
            name: Technical name (3-63 chars, lowercase alphanumeric with hyphens only)
            display_name: Human-friendly display name
            description: Optional description
            timezone: TimeZone ID (e.g., "America/New_York"), defaults to UTC
            max_users: Maximum number of users (default: 1)
            max_analyst: Maximum number of analysts (default: 1)
            max_cases: Maximum number of cases (None = unlimited)
            expiration_date: When the tenant expires (for trial tenants).
                Can be a datetime object or ISO format string.

        Returns:
            TenantCreated with new tenant details

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            ValidationError: If validation fails
            ConflictError: If tenant name already exists
        """
        payload = {
            "name": name,
            "displayName": display_name,
            "maxUsers": max_users,
            "maxAnalyst": max_analyst,
        }

        if description:
            payload["description"] = description
        if timezone:
            payload["timeZone"] = timezone
        if max_cases is not None:
            payload["maxCases"] = max_cases
        if expiration_date is not None:
            if isinstance(expiration_date, datetime):
                payload["expirationDate"] = expiration_date.isoformat()
            else:
                payload["expirationDate"] = expiration_date

        response = self._request("POST", "api/tenant", json_data=payload)
        return TenantCreated(**response)

    def update_tenant(
        self,
        tenant_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        timezone: Optional[str] = None,
        max_users: Optional[int] = None,
        max_analyst: Optional[int] = None,
        max_cases: Optional[int] = None,
        is_academic: Optional[bool] = None,
        pre_release: Optional[bool] = None,
        is_disabled: Optional[bool] = None,
        expiration_date: Optional[Union[datetime, str]] = None,
    ) -> TenantUpdated:
        """Update an existing tenant.

        Only provided (non-None) fields will be updated.

        Args:
            tenant_id: The tenant GUID (required)
            display_name: New display name
            description: New description
            timezone: New timezone ID
            max_users: New max users
            max_analyst: New max analysts
            max_cases: New max cases (-1 for unlimited)
            is_academic: Academic tenant flag
            pre_release: Pre-release features flag
            is_disabled: Disable tenant (blocks all user logins)
            expiration_date: New expiration date (for trial tenants).
                Can be a datetime object or ISO format string.
                Set to empty string or past date to remove expiration.

        Returns:
            TenantUpdated with updated tenant details

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If tenant not found
            ValueError: If tenant_id is not a valid GUID
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")

        # Build payload with only provided fields
        payload = {"tenantId": tenant_id}

        if display_name is not None:
            payload["displayName"] = display_name
        if description is not None:
            payload["description"] = description
        if timezone is not None:
            payload["timeZone"] = timezone
        if max_users is not None:
            payload["maxUsers"] = max_users
        if max_analyst is not None:
            payload["maxAnalyst"] = max_analyst
        if max_cases is not None:
            payload["maxCases"] = max_cases
        if is_academic is not None:
            payload["isAcademic"] = is_academic
        if pre_release is not None:
            payload["preRelease"] = pre_release
        if is_disabled is not None:
            payload["isDisabled"] = is_disabled
        if expiration_date is not None:
            if isinstance(expiration_date, datetime):
                payload["expirationDate"] = expiration_date.isoformat()
            else:
                payload["expirationDate"] = expiration_date

        response = self._request("PUT", "api/tenant", json_data=payload)
        return TenantUpdated(**response)

    def delete_tenant(
        self,
        tenant_id: str,
        name: str,
        display_name: str,
    ) -> Dict[str, Any]:
        """Delete a tenant (requires triple verification).

        SAFETY: All three identifiers (ID, name, display name) must match exactly.
        This ensures you know exactly which tenant you're deleting.

        WARNING: This operation is IRREVERSIBLE. All tenant data will be
        permanently deleted including projects, datasets, and blob storage.

        Args:
            tenant_id: The tenant GUID
            name: The technical name (must match exactly)
            display_name: The display name (must match exactly)

        Returns:
            Dict with deletion result including:
            - message: Success message
            - tenantName: Deleted tenant's name
            - tenantDisplayName: Deleted tenant's display name
            - storageContainerDeleted: Whether blob storage was deleted

        Raises:
            AuthenticationError: If not using a GLOBAL API key
            NotFoundError: If tenant not found
            ValidationError: If name or display_name don't match
            ValueError: If tenant_id is not a valid GUID
        """
        if not validate_guid(tenant_id):
            raise ValueError(f"Invalid tenant ID format: {tenant_id}")

        payload = {
            "tenantId": tenant_id,
            "name": name,
            "displayName": display_name,
        }

        return self._request("DELETE", "api/tenant", json_data=payload)

    def get_all_tenants(self) -> List[TenantListItem]:
        """Get all tenants (convenience method with auto-pagination).

        Returns:
            List of all tenants

        Raises:
            AuthenticationError: If not using a GLOBAL API key
        """
        all_tenants = []
        page = 1
        page_size = 100

        while True:
            response = self.list_tenants(page=page, page_size=page_size)
            all_tenants.extend(response.tenants)

            if not response.has_next:
                break

            page += 1

        return all_tenants
