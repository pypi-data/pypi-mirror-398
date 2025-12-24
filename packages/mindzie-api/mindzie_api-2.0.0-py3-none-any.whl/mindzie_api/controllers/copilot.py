"""Copilot notebook controller for Mindzie API."""

from typing import Optional, Dict, Any, List
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid

logger = logging.getLogger(__name__)


class CopilotController(BaseController):
    """Controller for copilot notebook endpoints."""
    
    def run_notebook_template(
        self,
        project_id: str,
        dataset_id: str,
        investigation_id: Optional[str] = None,
        notebook_template_id: Optional[str] = None,
        output_type: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a notebook template with copilot.
        
        Args:
            project_id: Project ID
            dataset_id: Dataset ID
            investigation_id: Optional investigation ID
            notebook_template_id: Optional notebook template ID
            output_type: Optional output type
            prompt: Optional prompt for copilot
            
        Returns:
            Copilot notebook execution result
        """
        if not validate_guid(project_id) or not validate_guid(dataset_id):
            raise ValueError("Invalid project or dataset ID format")
        
        request_data = {
            "ProjectId": project_id,
            "DatasetId": dataset_id
        }
        
        if investigation_id:
            request_data["InvestigationId"] = investigation_id
        if notebook_template_id:
            request_data["NotebookTemplateId"] = notebook_template_id
        if output_type:
            request_data["OutputType"] = output_type
        if prompt:
            request_data["Prompt"] = prompt
        
        return self._request(
            "POST",
            "api/run-copilot-notebook/run-notebook-template",
            json_data=request_data
        )
    
    def run_notebook(
        self,
        project_id: str,
        dataset_id: str,
        notebook_id: str,
        investigation_id: Optional[str] = None,
        output_type: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run an existing notebook with copilot.
        
        Args:
            project_id: Project ID
            dataset_id: Dataset ID
            notebook_id: Notebook ID to run
            investigation_id: Optional investigation ID
            output_type: Optional output type
            prompt: Optional prompt for copilot
            
        Returns:
            Copilot notebook execution result
        """
        if not validate_guid(project_id) or not validate_guid(dataset_id) or not validate_guid(notebook_id):
            raise ValueError("Invalid ID format")
        
        request_data = {
            "ProjectId": project_id,
            "DatasetId": dataset_id,
            "NotebookId": notebook_id
        }
        
        if investigation_id:
            request_data["InvestigationId"] = investigation_id
        if output_type:
            request_data["OutputType"] = output_type
        if prompt:
            request_data["Prompt"] = prompt
        
        return self._request(
            "POST",
            "api/run-copilot-notebook/run-notebook",
            json_data=request_data
        )
    
    def get_available_outputs(
        self,
        dataset_id: str,
        investigation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available copilot outputs for a dataset or investigation.
        
        Args:
            dataset_id: Dataset ID
            investigation_id: Optional investigation ID
            
        Returns:
            List of available copilot outputs
        """
        if not validate_guid(dataset_id):
            raise ValueError("Invalid dataset ID format")
        
        params = {"datasetId": dataset_id}
        if investigation_id:
            if not validate_guid(investigation_id):
                raise ValueError("Invalid investigation ID format")
            params["investigationId"] = investigation_id
        
        response = self._request(
            "GET",
            "api/run-copilot-notebook/available-outputs",
            params=params
        )
        
        # Return as list if response is a list, otherwise wrap in list
        if isinstance(response, list):
            return response
        return response.get("outputs", [])