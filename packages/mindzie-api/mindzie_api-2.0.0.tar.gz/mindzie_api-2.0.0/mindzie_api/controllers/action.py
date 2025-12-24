"""Action controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class ActionController(BaseController):
    """Controller for action-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "action/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "action/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def execute(self, project_id: str, action_id: str) -> Dict[str, Any]:
        """Execute action."""
        return self._request("GET", f"action/execute/{action_id}", project_id=project_id)
