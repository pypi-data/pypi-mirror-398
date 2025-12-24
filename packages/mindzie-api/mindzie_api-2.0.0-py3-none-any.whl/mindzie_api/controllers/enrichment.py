"""Enrichment controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class EnrichmentController(BaseController):
    """Controller for enrichment-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "enrichment/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "enrichment/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    def get_all(self, project_id: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get all enrichments."""
        params = build_query_params(page=page, page_size=page_size)
        return self._request("GET", "enrichment", project_id=project_id, params=params)
    
    def get_by_id(self, project_id: str, enrichment_id: str) -> Dict[str, Any]:
        """Get enrichment by ID."""
        return self._request("GET", f"enrichment/{enrichment_id}", project_id=project_id)
    
    def get_notebooks(self, project_id: str, enrichment_id: str) -> Dict[str, Any]:
        """Get notebooks for enrichment."""
        return self._request("GET", f"enrichment/{enrichment_id}/notebooks", project_id=project_id)
    
    def execute(self, project_id: str, enrichment_id: str) -> Dict[str, Any]:
        """Execute enrichment."""
        return self._request("POST", f"enrichment/{enrichment_id}/execute", project_id=project_id)
