"""Execution controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class ExecutionController(BaseController):
    """Controller for execution-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "execution/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "execution/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def get_queue(self, project_id: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get execution queue."""
        params = build_query_params(page=page, page_size=page_size)
        return self._request("GET", "execution/queue", project_id=project_id, params=params)
    
    def queue_notebook(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Queue notebook for execution."""
        return self._request("POST", f"execution/queue/notebook/{notebook_id}", project_id=project_id)
    
    def queue_investigation(self, project_id: str, investigation_id: str) -> Dict[str, Any]:
        """Queue investigation for execution."""
        return self._request("POST", f"execution/queue/investigation/{investigation_id}", project_id=project_id)
    
    def cancel(self, project_id: str, execution_id: str) -> Dict[str, Any]:
        """Cancel execution."""
        return self._request("DELETE", f"execution/queue/{execution_id}", project_id=project_id)
    
    def get_status(self, project_id: str, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        return self._request("GET", f"execution/status/{execution_id}", project_id=project_id)
    
    def get_history(self, project_id: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get execution history."""
        params = build_query_params(page=page, page_size=page_size)
        return self._request("GET", "execution/history", project_id=project_id, params=params)
