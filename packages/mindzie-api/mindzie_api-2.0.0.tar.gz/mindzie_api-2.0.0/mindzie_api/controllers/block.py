"""Block controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class BlockController(BaseController):
    """Controller for block-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "block/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "block/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def get(self, project_id: str, block_id: str) -> Dict[str, Any]:
        """Get block by ID."""
        return self._request("GET", f"block/{block_id}", project_id=project_id)
    
    def update(self, project_id: str, block_id: str, **kwargs) -> Dict[str, Any]:
        """Update block."""
        return self._request("PUT", f"block/{block_id}", project_id=project_id, json_data=kwargs)
    
    def delete(self, project_id: str, block_id: str) -> Dict[str, Any]:
        """Delete block."""
        return self._request("DELETE", f"block/{block_id}", project_id=project_id)
    
    def execute(self, project_id: str, block_id: str, **kwargs) -> Dict[str, Any]:
        """Execute block."""
        return self._request("POST", f"block/{block_id}/execute", project_id=project_id, json_data=kwargs)
    
    def get_results(self, project_id: str, block_id: str) -> Dict[str, Any]:
        """Get block execution results."""
        return self._request("GET", f"block/{block_id}/results", project_id=project_id)
    
    def get_output_data(self, project_id: str, block_id: str) -> Dict[str, Any]:
        """Get block output data."""
        return self._request("GET", f"block/{block_id}/output-data", project_id=project_id)
    
    def create_filter(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """Create filter block."""
        return self._request("POST", "block/filter", project_id=project_id, json_data=kwargs)
    
    def create_calculator(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """Create calculator block."""
        return self._request("POST", "block/calculator", project_id=project_id, json_data=kwargs)
    
    def create_alert(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """Create alert block."""
        return self._request("POST", "block/alert", project_id=project_id, json_data=kwargs)
