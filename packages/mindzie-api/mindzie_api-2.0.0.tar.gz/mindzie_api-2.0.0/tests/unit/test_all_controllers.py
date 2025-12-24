"""Comprehensive unit tests for all controllers.

This file tests that every controller method is callable and handles responses correctly.
"""

import pytest
import responses
import json
from unittest.mock import Mock, patch

from mindzie_api import MindzieAPIClient
from mindzie_api.exceptions import MindzieAPIException


@pytest.mark.unit
class TestAllControllers:
    """Test all controller methods are callable."""
    
    def test_all_controllers_exist(self, api_client):
        """Test that all controllers are accessible."""
        controllers = [
            'projects', 'datasets', 'investigations', 'notebooks', 
            'blocks', 'execution', 'enrichments', 'dashboards',
            'actions', 'action_executions', 'ping'
        ]
        
        for controller_name in controllers:
            assert hasattr(api_client, controller_name), f"Controller {controller_name} not found"
            controller = getattr(api_client, controller_name)
            assert controller is not None, f"Controller {controller_name} is None"
    
    @pytest.mark.parametrize("controller_name,method_name,requires_project", [
        # Project controller
        ("projects", "ping_unauthorized", False),
        ("projects", "ping", False),
        ("projects", "get_all", False),
        ("projects", "get_by_id", False),
        ("projects", "get_summary", False),
        ("projects", "list_projects", False),
        ("projects", "search", False),
        
        # Dataset controller
        ("datasets", "ping_unauthorized", True),
        ("datasets", "ping", True),
        ("datasets", "get_all", True),
        ("datasets", "create_from_csv", True),
        ("datasets", "create_from_package", True),
        ("datasets", "create_from_binary", True),
        ("datasets", "update_from_csv", True),
        ("datasets", "update_from_package", True),
        ("datasets", "update_from_binary", True),
        
        # Investigation controller
        ("investigations", "ping_unauthorized", True),
        ("investigations", "ping", True),
        ("investigations", "get_all", True),
        ("investigations", "get_by_id", True),
        ("investigations", "create", True),
        ("investigations", "update", True),
        ("investigations", "delete", True),
        ("investigations", "get_notebooks", True),
        ("investigations", "get_main_notebook", True),
        
        # Notebook controller
        ("notebooks", "ping_unauthorized", True),
        ("notebooks", "ping", True),
        ("notebooks", "get_all", True),
        ("notebooks", "get", True),
        ("notebooks", "update", True),
        ("notebooks", "delete", True),
        ("notebooks", "get_blocks", True),
        ("notebooks", "add_block", True),
        ("notebooks", "execute", True),
        ("notebooks", "get_execution_status", True),
        ("notebooks", "get_url", True),
        
        # Block controller
        ("blocks", "ping_unauthorized", True),
        ("blocks", "ping", True),
        ("blocks", "get", True),
        ("blocks", "update", True),
        ("blocks", "delete", True),
        ("blocks", "execute", True),
        ("blocks", "get_results", True),
        ("blocks", "get_output_data", True),
        ("blocks", "create_filter", True),
        ("blocks", "create_calculator", True),
        ("blocks", "create_alert", True),
        
        # Execution controller
        ("execution", "ping_unauthorized", True),
        ("execution", "ping", True),
        ("execution", "get_queue", True),
        ("execution", "queue_notebook", True),
        ("execution", "queue_investigation", True),
        ("execution", "cancel", True),
        ("execution", "get_status", True),
        ("execution", "get_history", True),
        
        # Enrichment controller
        ("enrichments", "ping_unauthorized", True),
        ("enrichments", "ping", True),
        ("enrichments", "get_all", True),
        ("enrichments", "get_by_id", True),
        ("enrichments", "get_notebooks", True),
        ("enrichments", "execute", True),
        
        # Dashboard controller
        ("dashboards", "ping_unauthorized", True),
        ("dashboards", "ping", True),
        ("dashboards", "get_all", True),
        ("dashboards", "get_by_id", True),
        ("dashboards", "get_panels", True),
        ("dashboards", "get_url", True),
        
        # Action controller
        ("actions", "ping_unauthorized", True),
        ("actions", "ping", True),
        ("actions", "execute", True),
        
        # Action Execution controller
        ("action_executions", "ping_unauthorized", True),
        ("action_executions", "ping", True),
        ("action_executions", "get_by_action", True),
        ("action_executions", "get_last", True),
        ("action_executions", "get_by_id", True),
        ("action_executions", "download_package", True),
        
        # Ping controller
        ("ping", "ping_basic", False),
        ("ping", "ping_exception", False),
    ])
    def test_controller_method_exists(self, api_client, controller_name, method_name, requires_project):
        """Test that each controller method exists and is callable."""
        controller = getattr(api_client, controller_name, None)
        assert controller is not None, f"Controller {controller_name} not found"
        
        method = getattr(controller, method_name, None)
        assert method is not None, f"Method {controller_name}.{method_name} not found"
        assert callable(method), f"Method {controller_name}.{method_name} is not callable"
    
    def test_dataset_file_upload_methods(self, api_client, mock_responses, sample_csv_file):
        """Test dataset file upload methods."""
        project_id = "test-project-id"
        
        # Mock response for CSV upload
        mock_responses.add(
            responses.POST,
            f"{api_client.base_url}/api/{api_client.tenant_id}/{project_id}/dataset/csv",
            json={"DatasetId": "new-dataset-id", "Status": "Success"},
            status=200
        )
        
        # Test with file path
        result = api_client.datasets.create_from_csv(
            project_id=project_id,
            dataset_name="Test Dataset",
            case_id_column="case_id",
            activity_name_column="activity",
            activity_time_column="timestamp",
            csv_file=str(sample_csv_file)
        )
        
        assert result["DatasetId"] == "new-dataset-id"
        assert result["Status"] == "Success"
    
    def test_error_handling_across_controllers(self, api_client, mock_responses):
        """Test error handling is consistent across all controllers."""
        # Test 404 error
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project/nonexistent",
            json={"error": "Not found"},
            status=404
        )
        
        from mindzie_api.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            api_client.projects.get_by_id("nonexistent")
    
    def test_pagination_parameters(self, api_client, mock_responses):
        """Test that pagination works across controllers that support it."""
        controllers_with_pagination = [
            ("projects", "get_all", "project"),
            ("execution", "get_queue", "execution/queue"),
            ("execution", "get_history", "execution/history"),
            ("enrichments", "get_all", "enrichment"),
            ("dashboards", "get_all", "dashboard"),
        ]
        
        project_id = "test-project"
        
        for controller_name, method_name, endpoint in controllers_with_pagination:
            # Mock paginated response
            if controller_name == "projects":
                url = f"{api_client.base_url}/api/{api_client.tenant_id}/{endpoint}"
            else:
                url = f"{api_client.base_url}/api/{api_client.tenant_id}/{project_id}/{endpoint}"
            
            mock_responses.add(
                responses.GET,
                url,
                match=[responses.matchers.query_param_matcher({"page": "2", "pageSize": "25"})],
                json={"Items": [], "TotalCount": 100, "Page": 2, "PageSize": 25},
                status=200
            )
            
            controller = getattr(api_client, controller_name)
            method = getattr(controller, method_name)
            
            # Call with pagination parameters
            if controller_name == "projects":
                result = method(page=2, page_size=25)
            else:
                result = method(project_id, page=2, page_size=25)
            
            assert result is not None