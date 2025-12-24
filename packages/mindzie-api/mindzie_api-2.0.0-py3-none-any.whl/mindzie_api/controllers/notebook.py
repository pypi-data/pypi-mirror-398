"""Notebook controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class NotebookController(BaseController):
    """Controller for notebook-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "notebook/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "notebook/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def get_all(self, project_id: str, investigation_id: str) -> Dict[str, Any]:
        """Get all notebooks for investigation."""
        return self._request("GET", f"notebook/{investigation_id}", project_id=project_id)
    
    def get(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Get notebook by ID."""
        return self._request("GET", f"notebook/{notebook_id}", project_id=project_id)
    
    def update(self, project_id: str, notebook_id: str, **kwargs) -> Dict[str, Any]:
        """Update notebook."""
        return self._request("PUT", f"notebook/{notebook_id}", project_id=project_id, json_data=kwargs)
    
    def delete(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Delete notebook."""
        return self._request("DELETE", f"notebook/{notebook_id}", project_id=project_id)
    
    def get_blocks(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Get blocks in notebook."""
        return self._request("GET", f"notebook/{notebook_id}/blocks", project_id=project_id)
    
    def add_block(self, project_id: str, notebook_id: str, **kwargs) -> Dict[str, Any]:
        """Add block to notebook."""
        return self._request("POST", f"notebook/{notebook_id}/blocks", project_id=project_id, json_data=kwargs)
    
    def execute(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Execute notebook."""
        return self._request("POST", f"notebook/{notebook_id}/execute", project_id=project_id)
    
    def get_execution_status(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Get notebook execution status."""
        return self._request("GET", f"notebook/{notebook_id}/execution-status", project_id=project_id)
    
    def get_url(self, project_id: str, notebook_id: str) -> Dict[str, Any]:
        """Get notebook URL."""
        return self._request("GET", f"notebook/{notebook_id}/url", project_id=project_id)
