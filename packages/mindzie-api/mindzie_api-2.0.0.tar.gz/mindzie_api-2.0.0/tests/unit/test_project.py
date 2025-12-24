"""Unit tests for Project controller."""

import json
import pytest
import responses

from mindzie_api.exceptions import NotFoundError, ValidationError


@pytest.mark.unit
class TestProjectController:
    """Test suite for Project controller."""
    
    def test_ping_unauthorized(self, api_client, mock_responses):
        """Test unauthorized ping endpoint."""
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project/unauthorized-ping",
            body="Ping Successful",
            status=200
        )
        
        result = api_client.projects.ping_unauthorized()
        assert result == "Ping Successful"
        assert len(mock_responses.calls) == 1
    
    def test_ping_authenticated(self, api_client, mock_responses):
        """Test authenticated ping endpoint."""
        expected_response = f"Ping Successful (tenant id: {api_client.tenant_id})"
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project/ping",
            json={"data": expected_response},
            status=200
        )
        
        result = api_client.projects.ping()
        assert result == expected_response
        assert len(mock_responses.calls) == 1
    
    def test_get_all_projects(self, api_client, mock_responses, sample_project_data):
        """Test getting all projects."""
        response_data = {
            "Projects": [sample_project_data],
            "TotalCount": 1,
            "Page": 1,
            "PageSize": 50
        }
        
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            json=response_data,
            status=200
        )
        
        result = api_client.projects.get_all()
        assert len(result.projects) == 1
        assert result.total_count == 1
        assert result.page == 1
        assert result.projects[0].project_id == sample_project_data["ProjectId"]
        assert result.projects[0].project_name == sample_project_data["ProjectName"]
    
    def test_get_all_projects_with_pagination(self, api_client, mock_responses):
        """Test pagination parameters."""
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            match=[responses.matchers.query_param_matcher({"page": "2", "pageSize": "10"})],
            json={"Projects": [], "TotalCount": 100, "Page": 2, "PageSize": 10},
            status=200
        )
        
        result = api_client.projects.get_all(page=2, page_size=10)
        assert result.page == 2
        assert result.page_size == 10
        assert result.total_count == 100
        assert result.has_previous is True
        assert result.previous_page == 1
    
    def test_get_project_by_id(self, api_client, mock_responses, sample_project_data):
        """Test getting project by ID."""
        project_id = sample_project_data["ProjectId"]
        
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project/{project_id}",
            json=sample_project_data,
            status=200
        )
        
        result = api_client.projects.get_by_id(project_id)
        assert result.project_id == project_id
        assert result.project_name == sample_project_data["ProjectName"]
        assert result.tenant_id == sample_project_data["TenantId"]
    
    def test_get_project_by_id_invalid_guid(self, api_client):
        """Test getting project with invalid GUID."""
        with pytest.raises(ValueError, match="Invalid project ID format"):
            api_client.projects.get_by_id("invalid-guid")
    
    def test_get_project_by_id_not_found(self, api_client, mock_responses):
        """Test getting non-existent project."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project/{project_id}",
            json={"error": "Project not found"},
            status=404
        )
        
        with pytest.raises(NotFoundError):
            api_client.projects.get_by_id(project_id)
    
    def test_get_project_summary(self, api_client, mock_responses):
        """Test getting project summary."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        summary_data = {
            "ProjectId": project_id,
            "TenantId": api_client.tenant_id,
            "ProjectName": "Test Project",
            "TotalDatasets": 5,
            "TotalInvestigations": 10,
            "TotalDashboards": 3,
            "TotalActions": 15,
            "TotalUsers": 8,
            "LastActivity": "2024-01-15T10:30:00Z",
            "StorageUsedMB": 1024.5
        }
        
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project/{project_id}/summary",
            json=summary_data,
            status=200
        )
        
        result = api_client.projects.get_summary(project_id)
        assert result.project_id == project_id
        assert result.total_datasets == 5
        assert result.total_investigations == 10
        assert result.storage_used_mb == 1024.5
    
    def test_list_all_projects_auto_pagination(self, api_client, mock_responses):
        """Test automatic pagination in list_projects method."""
        # First page
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            match=[responses.matchers.query_param_matcher({"page": "1", "pageSize": "100"})],
            json={
                "Projects": [{"ProjectId": f"proj-{i}", "ProjectName": f"Project {i}"} 
                            for i in range(100)],
                "TotalCount": 150,
                "Page": 1,
                "PageSize": 100
            },
            status=200
        )
        
        # Second page
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            match=[responses.matchers.query_param_matcher({"page": "2", "pageSize": "100"})],
            json={
                "Projects": [{"ProjectId": f"proj-{i}", "ProjectName": f"Project {i}"} 
                            for i in range(100, 150)],
                "TotalCount": 150,
                "Page": 2,
                "PageSize": 100
            },
            status=200
        )
        
        all_projects = api_client.projects.list_projects()
        assert len(all_projects) == 150
        assert all_projects[0].project_id == "proj-0"
        assert all_projects[149].project_id == "proj-149"
    
    def test_search_projects(self, api_client, mock_responses):
        """Test searching projects with filters."""
        projects_data = [
            {"ProjectId": "1", "ProjectName": "Alpha Project", "IsActive": True, "DatasetCount": 5},
            {"ProjectId": "2", "ProjectName": "Beta Project", "IsActive": False, "DatasetCount": 3},
            {"ProjectId": "3", "ProjectName": "Gamma Alpha", "IsActive": True, "DatasetCount": 10},
        ]
        
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            json={"Projects": projects_data, "TotalCount": 3, "Page": 1, "PageSize": 1000},
            status=200
        )
        
        # Search by name
        result = api_client.projects.search(name_contains="Alpha")
        assert len(result.projects) == 2
        assert all("Alpha" in p.project_name for p in result.projects)
        
        # Search by active status
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            json={"Projects": projects_data, "TotalCount": 3, "Page": 1, "PageSize": 1000},
            status=200
        )
        
        result = api_client.projects.search(is_active=True)
        assert len(result.projects) == 2
        assert all(p.is_active for p in result.projects)
        
        # Search by minimum datasets
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            json={"Projects": projects_data, "TotalCount": 3, "Page": 1, "PageSize": 1000},
            status=200
        )
        
        result = api_client.projects.search(min_datasets=5)
        assert len(result.projects) == 2
        assert all(p.dataset_count >= 5 for p in result.projects)
    
    def test_error_handling_server_error(self, api_client, mock_responses):
        """Test handling of server errors."""
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            json={"error": "Internal server error"},
            status=500
        )
        
        from mindzie_api.exceptions import ServerError
        with pytest.raises(ServerError):
            api_client.projects.get_all()
    
    def test_error_handling_authentication(self, api_client, mock_responses):
        """Test handling of authentication errors."""
        mock_responses.add(
            responses.GET,
            f"{api_client.base_url}/api/{api_client.tenant_id}/project",
            json={"error": "Unauthorized"},
            status=401
        )
        
        from mindzie_api.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError):
            api_client.projects.get_all()