"""Dashboard controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class DashboardController(BaseController):
    """Controller for dashboard-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "dashboard/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "dashboard/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def get_all(self, project_id: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get all dashboards."""
        params = build_query_params(page=page, page_size=page_size)
        return self._request("GET", "dashboard", project_id=project_id, params=params)
    
    def get_by_id(self, project_id: str, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard by ID."""
        return self._request("GET", f"dashboard/{dashboard_id}", project_id=project_id)
    
    def get_panels(self, project_id: str, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard panels."""
        return self._request("GET", f"dashboard/{dashboard_id}/panels", project_id=project_id)
    
    def get_url(self, project_id: str, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard URL."""
        return self._request("GET", f"dashboard/{dashboard_id}/url", project_id=project_id)
