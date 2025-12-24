"""Pytest configuration and fixtures for mindzie-api tests."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest
import responses
from faker import Faker

from mindzie_api import MindzieAPIClient
from mindzie_api.auth import APIKeyAuth
from mindzie_api.constants import AuthType


# Initialize Faker for test data generation
fake = Faker()


# Test configuration
TEST_BASE_URL = "https://test.mindziestudio.com"
TEST_TENANT_ID = "test-tenant-123"
TEST_PROJECT_ID = "test-project-456"
TEST_API_KEY = "test-api-key-789"


@pytest.fixture
def test_config() -> Dict[str, str]:
    """Provide test configuration."""
    return {
        "base_url": TEST_BASE_URL,
        "tenant_id": TEST_TENANT_ID,
        "project_id": TEST_PROJECT_ID,
        "api_key": TEST_API_KEY,
    }


@pytest.fixture
def api_client(test_config) -> MindzieAPIClient:
    """Create a test API client."""
    return MindzieAPIClient(
        base_url=test_config["base_url"],
        tenant_id=test_config["tenant_id"],
        auth_type=AuthType.API_KEY,
        api_key=test_config["api_key"],
        timeout=5,
        max_retries=1
    )


@pytest.fixture
def mock_responses():
    """Activate responses mock for HTTP requests."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def sample_project_data() -> Dict[str, Any]:
    """Generate sample project data."""
    return {
        "ProjectId": fake.uuid4(),
        "TenantId": TEST_TENANT_ID,
        "ProjectName": fake.company(),
        "ProjectDescription": fake.text(max_nb_chars=200),
        "DateCreated": fake.date_time().isoformat(),
        "DateModified": fake.date_time().isoformat(),
        "CreatedBy": fake.uuid4(),
        "ModifiedBy": fake.uuid4(),
        "IsActive": True,
        "DatasetCount": fake.random_int(0, 10),
        "InvestigationCount": fake.random_int(0, 20),
        "DashboardCount": fake.random_int(0, 15),
        "UserCount": fake.random_int(1, 50),
    }


@pytest.fixture
def sample_dataset_data() -> Dict[str, Any]:
    """Generate sample dataset data."""
    return {
        "DatasetId": fake.uuid4(),
        "DatasetName": fake.word() + "_dataset",
        "DatasetDescription": fake.text(max_nb_chars=200),
        "ProjectId": TEST_PROJECT_ID,
        "DateCreated": fake.date_time().isoformat(),
        "DateModified": fake.date_time().isoformat(),
        "CreatedBy": fake.uuid4(),
        "ModifiedBy": fake.uuid4(),
        "UseDateOnlySorting": fake.boolean(),
        "UseOnlyEventColumns": fake.boolean(),
        "CaseIdColumnName": "case_id",
        "ActivityColumnName": "activity",
        "TimeColumnName": "timestamp",
        "ResourceColumnName": "resource",
        "BeginTimeColumnName": "start_time",
        "ExpectedOrderColumnName": "order",
    }


@pytest.fixture
def sample_investigation_data() -> Dict[str, Any]:
    """Generate sample investigation data."""
    return {
        "InvestigationId": fake.uuid4(),
        "ProjectId": TEST_PROJECT_ID,
        "InvestigationName": fake.word() + "_investigation",
        "InvestigationDescription": fake.text(max_nb_chars=200),
        "DatasetId": fake.uuid4(),
        "DateCreated": fake.date_time().isoformat(),
        "DateModified": fake.date_time().isoformat(),
        "CreatedBy": fake.uuid4(),
        "ModifiedBy": fake.uuid4(),
        "InvestigationOrder": fake.random_int(1, 100),
        "IsUsedForOperationCenter": fake.boolean(),
        "InvestigationFolderId": fake.uuid4(),
        "NotebookCount": fake.random_int(0, 10),
    }


@pytest.fixture
def sample_notebook_data() -> Dict[str, Any]:
    """Generate sample notebook data."""
    return {
        "NotebookId": fake.uuid4(),
        "InvestigationId": fake.uuid4(),
        "NotebookName": fake.word() + "_notebook",
        "NotebookDescription": fake.text(max_nb_chars=200),
        "DateCreated": fake.date_time().isoformat(),
        "DateModified": fake.date_time().isoformat(),
        "CreatedBy": fake.uuid4(),
        "ModifiedBy": fake.uuid4(),
        "IsMainNotebook": fake.boolean(),
        "BlockCount": fake.random_int(0, 20),
        "ExecutionStatus": "Completed",
    }


@pytest.fixture
def sample_block_data() -> Dict[str, Any]:
    """Generate sample block data."""
    return {
        "BlockId": fake.uuid4(),
        "NotebookId": fake.uuid4(),
        "BlockName": fake.word() + "_block",
        "BlockType": fake.random_element(["filter", "calculator", "alert", "enrichment"]),
        "BlockOrder": fake.random_int(1, 100),
        "Configuration": json.dumps({"key": "value"}),
        "DateCreated": fake.date_time().isoformat(),
        "DateModified": fake.date_time().isoformat(),
        "CreatedBy": fake.uuid4(),
        "ModifiedBy": fake.uuid4(),
        "LastExecutionTime": fake.date_time().isoformat(),
        "LastExecutionStatus": "Success",
    }


@pytest.fixture
def sample_csv_file(tmp_path) -> Path:
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "test_dataset.csv"
    csv_content = """case_id,activity,timestamp,resource
    case1,Start,2024-01-01 10:00:00,User1
    case1,Process,2024-01-01 11:00:00,User2
    case1,End,2024-01-01 12:00:00,User1
    case2,Start,2024-01-01 13:00:00,User3
    case2,Process,2024-01-01 14:00:00,User2
    case2,End,2024-01-01 15:00:00,User3
    """
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def mock_auth_provider():
    """Create a mock authentication provider."""
    provider = Mock(spec=APIKeyAuth)
    provider.get_headers.return_value = {
        "Authorization": f"Bearer {TEST_API_KEY}"
    }
    provider.is_valid.return_value = True
    provider.refresh.return_value = None
    return provider


@pytest.fixture
def env_setup(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("MINDZIE_API_URL", TEST_BASE_URL)
    monkeypatch.setenv("MINDZIE_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("MINDZIE_API_KEY", TEST_API_KEY)
    yield
    # Cleanup happens automatically with monkeypatch


@pytest.fixture
def capture_requests():
    """Capture all HTTP requests made during test."""
    captured = []
    
    def capture_callback(request):
        captured.append({
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "body": request.body,
        })
        return (200, {}, json.dumps({"success": True}))
    
    with responses.RequestsMock() as rsps:
        rsps.add_callback(
            responses.CallbackResponse(
                method=responses.GET,
                url=responses.matchers.any_url(),
                callback=capture_callback
            )
        )
        rsps.add_callback(
            responses.CallbackResponse(
                method=responses.POST,
                url=responses.matchers.any_url(),
                callback=capture_callback
            )
        )
        rsps.add_callback(
            responses.CallbackResponse(
                method=responses.PUT,
                url=responses.matchers.any_url(),
                callback=capture_callback
            )
        )
        rsps.add_callback(
            responses.CallbackResponse(
                method=responses.DELETE,
                url=responses.matchers.any_url(),
                callback=capture_callback
            )
        )
        yield captured


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_api: Tests requiring API access")