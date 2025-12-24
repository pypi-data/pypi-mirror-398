"""Investigation controller for Mindzie API."""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, build_query_params

logger = logging.getLogger(__name__)


class InvestigationController(BaseController):
    """Controller for investigation-related API endpoints."""

    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.

        Args:
            project_id: Project ID

        Returns:
            Ping response message
        """
        response = self._request("GET", "investigation/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")

    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.

        Args:
            project_id: Project ID

        Returns:
            Ping response message
        """
        response = self._request("GET", "investigation/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")

    def get_all(self, project_id: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get all investigations for a project."""
        params = build_query_params(page=page, page_size=page_size)
        return self._request("GET", "investigation", project_id=project_id, params=params)

    def get_by_id(self, project_id: str, investigation_id: str) -> Dict[str, Any]:
        """Get investigation by ID."""
        return self._request("GET", f"investigation/{investigation_id}", project_id=project_id)

    def create(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """Create new investigation."""
        return self._request("POST", "investigation", project_id=project_id, json_data=kwargs)

    def delete(self, project_id: str, investigation_id: str) -> Dict[str, Any]:
        """Delete investigation."""
        return self._request("DELETE", f"investigation/{investigation_id}", project_id=project_id)

    def get_notebooks(self, project_id: str, investigation_id: str) -> Dict[str, Any]:
        """Get notebooks for investigation."""
        return self._request("GET", f"investigation/{investigation_id}/notebooks", project_id=project_id)

    def get_main_notebook(self, project_id: str, investigation_id: str) -> Dict[str, Any]:
        """Get main notebook for investigation."""
        return self._request("GET", f"investigation/{investigation_id}/main-notebook", project_id=project_id)

    def update(
        self,
        project_id: str,
        investigation_id: str,
        date_modified: Optional[Union[datetime, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Update investigation with optional optimistic locking.

        Args:
            project_id: Project ID
            investigation_id: Investigation ID
            date_modified: Last known modification timestamp for optimistic locking.
                If provided and doesn't match server value, raises ConflictError.
            **kwargs: Fields to update (name, description, etc.)

        Returns:
            Updated investigation data

        Raises:
            ConflictError: If date_modified doesn't match server value (409)
        """
        data = dict(kwargs)
        if date_modified is not None:
            if isinstance(date_modified, datetime):
                data["dateModified"] = date_modified.isoformat()
            else:
                data["dateModified"] = date_modified

        return self._request("PUT", f"investigation/{investigation_id}", project_id=project_id, json_data=data)

    # ========== Investigation Cloning ==========

    def clone(
        self,
        project_id: str,
        investigation_id: str,
        target_project_id: Optional[str] = None,
        target_dataset_id: Optional[str] = None,
        target_folder_id: Optional[str] = None,
        new_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clone an investigation.

        Args:
            project_id: Source project ID
            investigation_id: Investigation to clone
            target_project_id: Target project ID (for cross-project cloning)
            target_dataset_id: Target dataset ID
            target_folder_id: Target folder ID
            new_name: Name for the cloned investigation

        Returns:
            Dict with investigationId and message
        """
        payload = {}
        if target_project_id:
            payload["targetProjectId"] = target_project_id
        if target_dataset_id:
            payload["targetDatasetId"] = target_dataset_id
        if target_folder_id:
            payload["targetFolderId"] = target_folder_id
        if new_name:
            payload["newName"] = new_name

        return self._request("POST", f"investigation/{investigation_id}/clone",
                            project_id=project_id, json_data=payload if payload else None)

    # ========== Investigation Folders ==========

    def list_folders(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all folders for a project.

        Args:
            project_id: Project ID

        Returns:
            List of folder objects
        """
        response = self._request("GET", "investigation-folder", project_id=project_id)
        if isinstance(response, list):
            return response
        return response.get("folders", [])

    def create_folder(self, project_id: str, name: str) -> Dict[str, Any]:
        """Create a new investigation folder.

        Args:
            project_id: Project ID
            name: Folder name

        Returns:
            Created folder data
        """
        return self._request("POST", "investigation-folder",
                            project_id=project_id, json_data={"name": name})

    def update_folder(self, project_id: str, folder_id: str, name: str) -> Dict[str, Any]:
        """Update an investigation folder.

        Args:
            project_id: Project ID
            folder_id: Folder ID to update
            name: New folder name

        Returns:
            Updated folder data
        """
        return self._request("PUT", f"investigation-folder/{folder_id}",
                            project_id=project_id, json_data={"name": name})

    def delete_folder(self, project_id: str, folder_id: str) -> Dict[str, Any]:
        """Delete an investigation folder.

        Investigations in the folder are moved to "unfiled", not deleted.

        Args:
            project_id: Project ID
            folder_id: Folder ID to delete

        Returns:
            Deletion result
        """
        return self._request("DELETE", f"investigation-folder/{folder_id}", project_id=project_id)

    def move_to_folder(
        self,
        project_id: str,
        investigation_id: str,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Move an investigation to a folder.

        Args:
            project_id: Project ID
            investigation_id: Investigation to move
            folder_id: Target folder ID (None to move to "unfiled")

        Returns:
            Move result
        """
        payload = {"folderId": folder_id} if folder_id else {}
        return self._request("POST", f"investigation/{investigation_id}/move",
                            project_id=project_id, json_data=payload)
