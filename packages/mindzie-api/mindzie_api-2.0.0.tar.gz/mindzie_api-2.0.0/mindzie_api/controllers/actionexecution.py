"""ActionExecution controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class ActionExecutionController(BaseController):
    """Controller for actionexecution-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "actionexecution/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "actionexecution/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def get_by_action(self, project_id: str, action_id: str) -> Dict[str, Any]:
        """Get executions for action."""
        return self._request("GET", f"actionexecution/action/{action_id}", project_id=project_id)
    
    def get_last(self, project_id: str, action_id: str) -> Dict[str, Any]:
        """Get last execution for action."""
        return self._request("GET", f"actionexecution/lastaction/{action_id}", project_id=project_id)
    
    def get_by_id(self, project_id: str, execution_id: str) -> Dict[str, Any]:
        """Get execution by ID."""
        return self._request("GET", f"actionexecution/{execution_id}", project_id=project_id)
    
    def download_package(self, project_id: str, execution_id: str) -> Dict[str, Any]:
        """Download execution package."""
        return self._request("GET", f"actionexecution/downloadpackage/{execution_id}", project_id=project_id)
