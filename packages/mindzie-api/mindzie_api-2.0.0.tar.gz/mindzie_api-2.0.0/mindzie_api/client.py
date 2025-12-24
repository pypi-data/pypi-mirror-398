"""Main API client for Mindzie Studio."""

import os
import time
import logging
from typing import Optional, Dict, Any, Union, BinaryIO
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mindzie_api.__version__ import __version__
from mindzie_api.auth import AuthProvider, create_auth_provider
from mindzie_api.constants import (
    AuthType, DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY, HTTP_OK, HTTP_CREATED, HTTP_ACCEPTED,
    HTTP_NO_CONTENT, HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED,
    HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_CONFLICT, HTTP_RATE_LIMIT,
    HTTP_SERVER_ERROR
)
from mindzie_api.exceptions import (
    MindzieAPIException, AuthenticationError, ValidationError,
    NotFoundError, ServerError, RateLimitError, TimeoutError,
    ConnectionError, ConflictError
)
from mindzie_api.utils import calculate_retry_delay, parse_error_response

# Import controllers
from mindzie_api.controllers.project import ProjectController
from mindzie_api.controllers.dataset import DatasetController
from mindzie_api.controllers.investigation import InvestigationController
from mindzie_api.controllers.notebook import NotebookController
from mindzie_api.controllers.block import BlockController
from mindzie_api.controllers.execution import ExecutionController
from mindzie_api.controllers.enrichment import EnrichmentController
from mindzie_api.controllers.dashboard import DashboardController
from mindzie_api.controllers.action import ActionController
from mindzie_api.controllers.actionexecution import ActionExecutionController
from mindzie_api.controllers.ping import PingController
from mindzie_api.controllers.copilot import CopilotController
from mindzie_api.controllers.tenant import TenantController
from mindzie_api.controllers.user import UserController

logger = logging.getLogger(__name__)


class MindzieAPIClient:
    """Main client for interacting with the Mindzie Studio API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        auth_type: AuthType = AuthType.API_KEY,
        auth_provider: Optional[AuthProvider] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        verify_ssl: bool = True,
        proxies: Optional[Dict[str, str]] = None,
        **auth_kwargs
    ):
        """Initialize the Mindzie API client.
        
        Args:
            base_url: Base URL of the API (e.g., https://dev.mindziestudio.com)
            tenant_id: Tenant ID for multi-tenant operations
            auth_type: Type of authentication to use
            auth_provider: Custom auth provider (overrides auth_type)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            verify_ssl: Whether to verify SSL certificates
            proxies: Proxy configuration
            **auth_kwargs: Additional arguments for auth provider
        """
        # Get configuration from environment if not provided
        self.base_url = (base_url or os.getenv("MINDZIE_API_URL", "https://dev.mindziestudio.com")).rstrip("/")
        self.tenant_id = tenant_id or os.getenv("MINDZIE_TENANT_ID")
        
        if not self.tenant_id:
            raise ValueError("Tenant ID is required. Provide it directly or set MINDZIE_TENANT_ID environment variable.")
        
        # Validate max_retries parameter
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if max_retries > 10:  # Reasonable upper limit
            raise ValueError("max_retries must be <= 10 to prevent infinite loops")
        
        # Set up authentication
        self.auth_provider = auth_provider or create_auth_provider(auth_type, **auth_kwargs)
        
        # Configure session
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.proxies = proxies
        
        # Create session with retry strategy
        self.session = self._create_session()
        
        # Initialize controllers
        self._init_controllers()
        
        logger.info(f"Mindzie API client initialized for {self.base_url}")
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=DEFAULT_RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": f"mindzie-api-python/{__version__}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # Add authentication headers
        session.headers.update(self.auth_provider.get_headers())
        
        # Set SSL verification
        session.verify = self.verify_ssl
        
        # Set proxies if provided
        if self.proxies:
            session.proxies.update(self.proxies)
        
        return session
    
    def _init_controllers(self) -> None:
        """Initialize API controllers."""
        self.projects = ProjectController(self)
        self.datasets = DatasetController(self)
        self.investigations = InvestigationController(self)
        self.notebooks = NotebookController(self)
        self.blocks = BlockController(self)
        self.execution = ExecutionController(self)
        self.enrichments = EnrichmentController(self)
        self.dashboards = DashboardController(self)
        self.actions = ActionController(self)
        self.action_executions = ActionExecutionController(self)
        self.ping = PingController(self)
        self.copilot = CopilotController(self)
        self.tenants = TenantController(self)
        self.users = UserController(self)
    
    def request(
        self,
        method: str,
        endpoint: str,
        project_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], BinaryIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            project_id: Project ID for the request
            params: Query parameters
            json_data: JSON body data
            files: Files to upload
            data: Form data or binary data
            headers: Additional headers
            timeout: Request timeout override
            **kwargs: Additional request arguments
        
        Returns:
            Response data dictionary
        
        Raises:
            MindzieAPIException: On API errors
        """
        # Build URL
        if project_id:
            url = f"{self.base_url}/api/{self.tenant_id}/{project_id}/{endpoint.lstrip('/')}"
        elif endpoint.startswith("api/"):
            url = f"{self.base_url}/{endpoint}"
        else:
            url = f"{self.base_url}/api/{self.tenant_id}/{endpoint.lstrip('/')}"
        
        # Prepare request
        request_kwargs = {
            "method": method,
            "url": url,
            "params": params,
            "timeout": timeout or self.timeout
        }
        
        if json_data is not None:
            request_kwargs["json"] = json_data
        elif files is not None:
            request_kwargs["files"] = files
            # For multipart/form-data, we must not send Content-Type header
            # Let requests library set it with the proper boundary
            if headers is None:
                headers = {}
            # Merge headers and explicitly remove Content-Type for file uploads
            merged_headers = {**self.session.headers, **headers}
            if "Content-Type" in merged_headers:
                del merged_headers["Content-Type"]
            request_kwargs["headers"] = merged_headers
            # Include form data if provided
            if data is not None:
                request_kwargs["data"] = data
        elif data is not None:
            request_kwargs["data"] = data
        
        if headers and files is None:  # Only apply headers if not uploading files
            request_kwargs["headers"] = {**self.session.headers, **headers}
        
        request_kwargs.update(kwargs)
        
        # Make request with retries
        attempt = 0
        last_error = None
        max_total_time = 300  # 5 minute absolute maximum
        start_time = time.time()
        
        while attempt <= self.max_retries:  # Use <= to include initial attempt
            # Safety check for maximum total time
            if time.time() - start_time > max_total_time:
                raise MindzieAPIException(f"Request failed: exceeded maximum total time of {max_total_time} seconds")
            
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{self.max_retries + 1})")
                response = self.session.request(**request_kwargs)
                
                # Handle response
                return self._handle_response(response)
                
            except requests.exceptions.Timeout as e:
                last_error = TimeoutError(f"Request timed out: {str(e)}")
                attempt += 1
                if attempt <= self.max_retries:
                    delay = calculate_retry_delay(attempt)
                    logger.warning(f"Request timed out, retrying in {delay:.2f}s (attempt {attempt}/{self.max_retries + 1})")
                    time.sleep(delay)
                    
            except requests.exceptions.ConnectionError as e:
                last_error = ConnectionError(f"Connection failed: {str(e)}")
                attempt += 1
                if attempt <= self.max_retries:
                    delay = calculate_retry_delay(attempt)
                    logger.warning(f"Connection failed, retrying in {delay:.2f}s (attempt {attempt}/{self.max_retries + 1})")
                    time.sleep(delay)
                    
            except requests.exceptions.RequestException as e:
                # Don't retry on other request exceptions
                last_error = MindzieAPIException(f"Request failed: {str(e)}")
                break
            except Exception as e:
                # Catch any unexpected exceptions to prevent infinite loops
                last_error = MindzieAPIException(f"Unexpected error during request: {str(e)}")
                break
        
        # Raise the last error if all retries failed
        if last_error:
            raise last_error
        
        raise MindzieAPIException("Request failed after all retries")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response.
        
        Args:
            response: HTTP response object
        
        Returns:
            Response data dictionary
        
        Raises:
            MindzieAPIException: On API errors
        """
        # Extract request ID if available
        request_id = response.headers.get("X-Request-Id")
        
        # Handle successful responses
        if response.status_code in [HTTP_OK, HTTP_CREATED, HTTP_ACCEPTED]:
            try:
                json_data = response.json()
                # Validate that we got a dictionary or list response
                if not isinstance(json_data, (dict, list)):
                    logger.warning(f"API returned unexpected JSON type: {type(json_data)}")
                    return {"data": json_data, "status_code": response.status_code}
                return json_data
            except ValueError as e:
                # Return text response if not JSON
                logger.warning(f"Failed to parse JSON response: {e}")
                return {"data": response.text, "status_code": response.status_code}
            except Exception as e:
                # Handle any other JSON parsing errors
                logger.error(f"Unexpected error parsing JSON: {e}")
                return {"data": response.text, "status_code": response.status_code}
        
        # Handle no content
        if response.status_code == HTTP_NO_CONTENT:
            return {"success": True, "status_code": response.status_code}
        
        # Handle errors
        error_data = parse_error_response(response.text)
        error_message = error_data.get("error", response.reason)
        
        if response.status_code == HTTP_BAD_REQUEST:
            raise ValidationError(error_message, response.status_code, error_data, request_id)
        elif response.status_code == HTTP_UNAUTHORIZED:
            raise AuthenticationError(error_message, response.status_code, error_data, request_id)
        elif response.status_code == HTTP_FORBIDDEN:
            raise AuthenticationError(f"Forbidden: {error_message}", response.status_code, error_data, request_id)
        elif response.status_code == HTTP_NOT_FOUND:
            raise NotFoundError(error_message, response.status_code, error_data, request_id)
        elif response.status_code == HTTP_CONFLICT:
            date_modified = error_data.get("dateModified")
            raise ConflictError(error_message, date_modified=date_modified, status_code=response.status_code, response_data=error_data, request_id=request_id)
        elif response.status_code == HTTP_RATE_LIMIT:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(error_message, retry_after, status_code=response.status_code, response_data=error_data, request_id=request_id)
        elif response.status_code >= HTTP_SERVER_ERROR:
            raise ServerError(error_message, response.status_code, error_data, request_id)
        else:
            raise MindzieAPIException(error_message, response.status_code, error_data, request_id)
    
    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()