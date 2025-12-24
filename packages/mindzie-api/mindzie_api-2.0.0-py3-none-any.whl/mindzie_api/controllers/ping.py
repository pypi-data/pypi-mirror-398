"""Ping controller for Mindzie API."""

from typing import Optional, Dict, Any, BinaryIO
import logging

from mindzie_api.controllers import BaseController

logger = logging.getLogger(__name__)


class PingController(BaseController):
    """Controller for various ping and connectivity test endpoints."""
    
    def ping(self) -> str:
        """Basic ping test.
        
        Returns:
            Ping response message
        """
        response = self._request("GET", "api/ping/ping")
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_exception(self) -> str:
        """Ping with exception test.
        
        Returns:
            Ping exception response
        
        Raises:
            Exception: Intentional test exception
        """
        response = self._request("GET", "api/ping/ping-exception")
        return response if isinstance(response, str) else response.get("data", "Ping Exception")
    
    def unauthorized_ping(self) -> str:
        """Unauthorized ping test.
        
        Returns:
            Ping response without authentication
        """
        response = self._request("GET", "api/ping/unauthorizedping")
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_tenant_id(self, tenant_id: str) -> str:
        """Ping with tenant ID parameter.
        
        Args:
            tenant_id: Tenant ID to test
            
        Returns:
            Ping response with tenant information
        """
        response = self._request("GET", f"api/ping/pingwithtenantidpathparam/{tenant_id}")
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_project_id(self, project_id: str) -> str:
        """Ping with project ID parameter.
        
        Args:
            project_id: Project ID to test
            
        Returns:
            Ping response with project information
        """
        response = self._request("GET", f"api/ping/pingwithprojectidpathparam/{project_id}")
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_body(self, ping_data: Dict[str, Any]) -> str:
        """Ping with body parameter.
        
        Args:
            ping_data: Dictionary with ping data (id and name)
            
        Returns:
            Ping response with body data
        """
        response = self._request("GET", "api/ping/pingwithbodyparam", json_data=ping_data)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_path_and_body(self, id: int, ping_data: Dict[str, Any]) -> str:
        """Ping with path and body parameters.
        
        Args:
            id: Path parameter ID
            ping_data: Dictionary with ping data
            
        Returns:
            Ping response with combined data
        """
        response = self._request("GET", f"api/ping/pingwithpathandbodyparam/{id}", json_data=ping_data)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_file(self, file: BinaryIO, filename: str = "test.txt") -> str:
        """Ping with file upload.
        
        Args:
            file: File to upload
            filename: Name of the file
            
        Returns:
            Ping response with file information
        """
        files = {"file": (filename, file, "application/octet-stream")}
        response = self._request("POST", "api/ping/pingwithfileparam", files=files)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_multiple_form_params(
        self,
        ping_data: Dict[str, Any],
        file: BinaryIO,
        filename: str = "test.txt"
    ) -> str:
        """Ping with multiple form parameters.
        
        Args:
            ping_data: Dictionary with ping data
            file: File to upload
            filename: Name of the file
            
        Returns:
            Ping response with combined form data
        """
        files = {"file": (filename, file, "application/octet-stream")}
        response = self._request("POST", "api/ping/pingwithmultipleformparams", data=ping_data, files=files)
        return response if isinstance(response, str) else response.get("data", "Ping Successful")
    
    def ping_with_path_and_multiple_form_params(
        self,
        id: int,
        ping_data: Dict[str, Any],
        file: BinaryIO,
        filename: str = "test.txt"
    ) -> str:
        """Ping with path and multiple form parameters.
        
        Args:
            id: Path parameter ID
            ping_data: Dictionary with ping data
            file: File to upload
            filename: Name of the file
            
        Returns:
            Ping response with all combined data
        """
        files = {"file": (filename, file, "application/octet-stream")}
        response = self._request(
            "POST",
            f"api/ping/pingwithpathandmultipleformparams/{id}",
            data=ping_data,
            files=files
        )
        return response if isinstance(response, str) else response.get("data", "Ping Successful")