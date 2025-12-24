"""Controllers for Mindzie API endpoints."""

from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from mindzie_api.client import MindzieAPIClient


class BaseController:
    """Base class for API controllers."""
    
    def __init__(self, client: "MindzieAPIClient"):
        """Initialize controller with API client.
        
        Args:
            client: MindzieAPIClient instance
        """
        self.client = client
    
    def _request(
        self,
        method: str,
        endpoint: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make request through the client.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            project_id: Project ID for the request
            **kwargs: Additional request arguments
        
        Returns:
            Response data
        """
        return self.client.request(method, endpoint, project_id, **kwargs)