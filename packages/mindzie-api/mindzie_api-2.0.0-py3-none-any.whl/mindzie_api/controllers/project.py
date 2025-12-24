"""Project controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.models.project import Project, ProjectListResponse, ProjectSummary
from mindzie_api.utils import build_query_params, validate_guid

logger = logging.getLogger(__name__)


class ProjectController(BaseController):
    """Controller for project-related API endpoints."""
    
    def ping_unauthorized(self) -> str:
        """Test connectivity without authentication.
        
        Returns:
            Ping response message
        """
        response = self._request("GET", "project/unauthorized-ping")
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self) -> str:
        """Test authenticated connectivity.
        
        Returns:
            Ping response message with tenant ID
        """
        response = self._request("GET", "project/ping")
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def get_all(
        self,
        page: int = 1,
        page_size: int = 50
    ) -> ProjectListResponse:
        """Get all projects for the tenant.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
        
        Returns:
            ProjectListResponse with list of projects
        """
        params = build_query_params(page=page, page_size=page_size)
        response = self._request("GET", "project", params=params)
        return ProjectListResponse(**response)
    
    def get_by_id(self, project_id: str) -> Project:
        """Get project by ID.
        
        Args:
            project_id: Project unique identifier
        
        Returns:
            Project details
        
        Raises:
            NotFoundError: If project not found
            ValidationError: If project_id is invalid
        """
        if not validate_guid(project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        response = self._request("GET", f"project/{project_id}")
        return Project(**response)
    
    def get_summary(self, project_id: str) -> ProjectSummary:
        """Get project summary statistics.
        
        Args:
            project_id: Project unique identifier
        
        Returns:
            ProjectSummary with statistics
        
        Raises:
            NotFoundError: If project not found
            ValidationError: If project_id is invalid
        """
        if not validate_guid(project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        response = self._request("GET", f"project/{project_id}/summary")
        return ProjectSummary(**response)
    
    def list_projects(self, **kwargs) -> List[Project]:
        """List all projects (convenience method).
        
        This method automatically handles pagination to retrieve all projects.
        
        Args:
            **kwargs: Additional query parameters
        
        Returns:
            List of all projects
        """
        all_projects = []
        page = 1
        page_size = 100  # Use larger page size for efficiency
        
        while True:
            response = self.get_all(page=page, page_size=page_size)
            all_projects.extend(response.projects)
            
            if not response.has_next:
                break
            
            page += 1
        
        return all_projects
    
    def search(
        self,
        name_contains: Optional[str] = None,
        is_active: Optional[bool] = None,
        min_datasets: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> ProjectListResponse:
        """Search projects with filters.
        
        Args:
            name_contains: Filter by name containing this string
            is_active: Filter by active status
            min_datasets: Filter by minimum dataset count
            page: Page number
            page_size: Items per page
        
        Returns:
            Filtered project list
        """
        # Get all projects and filter client-side
        # (API doesn't support server-side filtering yet)
        all_response = self.get_all(page=1, page_size=1000)
        filtered_projects = all_response.projects
        
        if name_contains:
            name_lower = name_contains.lower()
            filtered_projects = [
                p for p in filtered_projects
                if name_lower in (p.project_name or "").lower()
            ]
        
        if is_active is not None:
            filtered_projects = [
                p for p in filtered_projects
                if p.is_active == is_active
            ]
        
        if min_datasets is not None:
            filtered_projects = [
                p for p in filtered_projects
                if p.dataset_count >= min_datasets
            ]
        
        # Apply pagination
        total_count = len(filtered_projects)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_projects = filtered_projects[start_idx:end_idx]
        
        return ProjectListResponse(
            projects=paginated_projects,
            total_count=total_count,
            page=page,
            page_size=page_size
        )