"""Dataset controller for Mindzie API."""

from typing import Optional, Dict, Any, List, Union, BinaryIO
from pathlib import Path
import logging

from mindzie_api.controllers import BaseController
from mindzie_api.utils import validate_guid, get_file_mime_type, format_file_size

logger = logging.getLogger(__name__)


class DatasetController(BaseController):
    """Controller for dataset-related API endpoints."""
    
    def ping_unauthorized(self, project_id: str) -> str:
        """Test connectivity without authentication.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "dataset/unauthorized-ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping(self, project_id: str) -> str:
        """Test authenticated connectivity.
        
        Args:
            project_id: Project ID
            
        Returns:
            Ping response message
        """
        response = self._request("GET", "dataset/ping", project_id=project_id)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def get_all(self, project_id: str) -> Dict[str, Any]:
        """Get all datasets for a project.
        
        Args:
            project_id: Project unique identifier
        
        Returns:
            Dictionary containing list of datasets
        """
        if not validate_guid(project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        return self._request("GET", "dataset", project_id=project_id)
    
    def create_from_csv(
        self,
        project_id: str,
        dataset_name: str,
        case_id_column: str,
        activity_name_column: str,
        activity_time_column: str,
        csv_file: Union[str, Path, BinaryIO],
        resource_column: Optional[str] = None,
        start_time_column: Optional[str] = None,
        culture_info: str = "en-US"
    ) -> Dict[str, Any]:
        """Create dataset from CSV file.
        
        Note: This method currently uses a placeholder implementation.
        The actual API endpoint structure needs to be verified.
        
        Args:
            project_id: Project ID
            dataset_name: Name for the dataset
            case_id_column: Column name for case ID
            activity_name_column: Column name for activity name
            activity_time_column: Column name for activity timestamp
            csv_file: Path to CSV file or file-like object
            resource_column: Optional column name for resource
            start_time_column: Optional column name for start time
            culture_info: Culture info for parsing (default: en-US)
        
        Returns:
            Created dataset information
        """
        if not validate_guid(project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        # Note: The actual API uses UploadCsv/UpdateLogWithCsvFile endpoint
        # This needs to be updated once the correct endpoint structure is confirmed
        
        # Prepare file - API expects 'File' (capital F) field name
        if isinstance(csv_file, (str, Path)):
            csv_file = Path(csv_file)
            if not csv_file.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_file}")
            
            with open(csv_file, "rb") as f:
                files = {"File": (csv_file.name, f, "text/csv")}
                
                # The actual endpoint appears to be different
                # Using direct URL construction for now
                params = {
                    "logId": project_id,  # API expects logId parameter
                    "delimiter": ",",
                    "culture": culture_info,
                    "encoding": "UTF-8"
                }
                
                # Use a direct endpoint call
                return self._client.request(
                    "POST",
                    "UploadCsv/UpdateLogWithCsvFile",
                    params=params,
                    files=files
                )
        else:
            # Handle file-like object
            files = {"File": ("dataset.csv", csv_file, "text/csv")}
            params = {
                "logId": project_id,
                "delimiter": ",",
                "culture": culture_info,
                "encoding": "UTF-8"
            }
            
            return self._client.request(
                "POST",
                "UploadCsv/UpdateLogWithCsvFile",
                params=params,
                files=files
            )
    
    def create_from_package(
        self,
        project_id: str,
        dataset_name: str,
        package_file: Union[str, Path, BinaryIO]
    ) -> Dict[str, Any]:
        """Create dataset from package file.
        
        Args:
            project_id: Project ID
            dataset_name: Name for the dataset
            package_file: Path to package file or file-like object
        
        Returns:
            Created dataset information
        """
        if not validate_guid(project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        form_data = {"datasetName": dataset_name}
        
        if isinstance(package_file, (str, Path)):
            package_file = Path(package_file)
            if not package_file.exists():
                raise FileNotFoundError(f"Package file not found: {package_file}")
            
            with open(package_file, "rb") as f:
                files = {"file": (package_file.name, f, get_file_mime_type(package_file))}
                return self._request(
                    "POST",
                    "dataset/package",
                    project_id=project_id,
                    data=form_data,
                    files=files
                )
        else:
            files = {"file": ("package.zip", package_file, "application/zip")}
            return self._request(
                "POST",
                "dataset/package",
                project_id=project_id,
                data=form_data,
                files=files
            )
    
    def create_from_binary(
        self,
        project_id: str,
        dataset_name: str,
        binary_file: Union[str, Path, BinaryIO]
    ) -> Dict[str, Any]:
        """Create dataset from binary file.
        
        WARNING: This endpoint may not exist in the current API.
        The implementation is provided for compatibility but may not work.
        
        Args:
            project_id: Project ID
            dataset_name: Name for the dataset
            binary_file: Path to binary file or file-like object
        
        Returns:
            Created dataset information
        
        Raises:
            NotImplementedError: If the endpoint doesn't exist
        """
        if not validate_guid(project_id):
            raise ValueError(f"Invalid project ID format: {project_id}")
        
        form_data = {"datasetName": dataset_name}
        
        if isinstance(binary_file, (str, Path)):
            binary_file = Path(binary_file)
            if not binary_file.exists():
                raise FileNotFoundError(f"Binary file not found: {binary_file}")
            
            # Log file size for large files
            file_size = binary_file.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                logger.info(f"Uploading large file: {format_file_size(file_size)}")
            
            with open(binary_file, "rb") as f:
                files = {"file": (binary_file.name, f, "application/octet-stream")}
                return self._request(
                    "POST",
                    "dataset/binary",
                    project_id=project_id,
                    data=form_data,
                    files=files
                )
        else:
            files = {"file": ("dataset.bin", binary_file, "application/octet-stream")}
            return self._request(
                "POST",
                "dataset/binary",
                project_id=project_id,
                data=form_data,
                files=files
            )
    
    def update_from_csv(
        self,
        project_id: str,
        dataset_id: str,
        case_id_column: str,
        activity_name_column: str,
        activity_time_column: str,
        csv_file: Union[str, Path, BinaryIO],
        resource_column: Optional[str] = None,
        start_time_column: Optional[str] = None,
        culture_info: str = "en-US"
    ) -> Dict[str, Any]:
        """Update dataset from CSV file.
        
        Note: Uses the UploadCsv/UpdateLogWithCsvFile endpoint.
        
        Args:
            project_id: Project ID
            dataset_id: Dataset ID to update
            case_id_column: Column name for case ID
            activity_name_column: Column name for activity name
            activity_time_column: Column name for activity timestamp
            csv_file: Path to CSV file or file-like object
            resource_column: Optional column name for resource
            start_time_column: Optional column name for start time
            culture_info: Culture info for parsing
        
        Returns:
            Updated dataset information
        """
        if not validate_guid(project_id) or not validate_guid(dataset_id):
            raise ValueError("Invalid project or dataset ID format")
        
        # Prepare file - API expects 'File' (capital F) field name
        if isinstance(csv_file, (str, Path)):
            csv_file = Path(csv_file)
            with open(csv_file, "rb") as f:
                files = {"File": (csv_file.name, f, "text/csv")}
                params = {
                    "logId": dataset_id,  # Use dataset_id as logId
                    "delimiter": ",",
                    "culture": culture_info,
                    "encoding": "UTF-8"
                }
                
                return self._client.request(
                    "POST",  # API uses POST for updates
                    "UploadCsv/UpdateLogWithCsvFile",
                    params=params,
                    files=files
                )
        else:
            files = {"File": ("dataset.csv", csv_file, "text/csv")}
            params = {
                "logId": dataset_id,
                "delimiter": ",",
                "culture": culture_info,
                "encoding": "UTF-8"
            }
            
            return self._client.request(
                "POST",
                "UploadCsv/UpdateLogWithCsvFile",
                params=params,
                files=files
            )
    
    def update_from_package(
        self,
        project_id: str,
        dataset_id: str,
        package_file: Union[str, Path, BinaryIO]
    ) -> Dict[str, Any]:
        """Update dataset from package file.
        
        Args:
            project_id: Project ID
            dataset_id: Dataset ID to update
            package_file: Path to package file or file-like object
        
        Returns:
            Updated dataset information
        """
        if not validate_guid(project_id) or not validate_guid(dataset_id):
            raise ValueError("Invalid project or dataset ID format")
        
        if isinstance(package_file, (str, Path)):
            package_file = Path(package_file)
            with open(package_file, "rb") as f:
                files = {"file": (package_file.name, f, get_file_mime_type(package_file))}
                return self._request(
                    "PUT",
                    f"dataset/{dataset_id}/package",
                    project_id=project_id,
                    files=files
                )
        else:
            files = {"file": ("package.zip", package_file, "application/zip")}
            return self._request(
                "PUT",
                f"dataset/{dataset_id}/package",
                project_id=project_id,
                files=files
            )
    
    def update_from_binary(
        self,
        project_id: str,
        dataset_id: str,
        binary_file: Union[str, Path, BinaryIO]
    ) -> Dict[str, Any]:
        """Update dataset from binary file.
        
        Args:
            project_id: Project ID
            dataset_id: Dataset ID to update
            binary_file: Path to binary file or file-like object
        
        Returns:
            Updated dataset information
        """
        if not validate_guid(project_id) or not validate_guid(dataset_id):
            raise ValueError("Invalid project or dataset ID format")
        
        if isinstance(binary_file, (str, Path)):
            binary_file = Path(binary_file)
            with open(binary_file, "rb") as f:
                files = {"file": (binary_file.name, f, "application/octet-stream")}
                return self._request(
                    "PUT",
                    f"dataset/{dataset_id}/binary",
                    project_id=project_id,
                    files=files
                )
        else:
            files = {"file": ("dataset.bin", binary_file, "application/octet-stream")}
            return self._request(
                "PUT",
                f"dataset/{dataset_id}/binary",
                project_id=project_id,
                files=files
            )