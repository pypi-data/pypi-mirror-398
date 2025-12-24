# Mindzie API Python Client

[![PyPI version](https://badge.fury.io/py/mindzie-api.svg)](https://badge.fury.io/py/mindzie-api)
[![Python Support](https://img.shields.io/pypi/pyversions/mindzie-api.svg)](https://pypi.org/project/mindzie-api/)
[![Documentation Status](https://readthedocs.org/projects/mindzie-api/badge/?version=latest)](https://docs.mindzie.com/api/python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python client library for the Mindzie Studio API. This library provides comprehensive access to all Mindzie Studio API endpoints with a clean, Pythonic interface.

## Features

- 🚀 **Complete API Coverage** - Access to all Mindzie Studio API endpoints
- 🔐 **Multiple Authentication Methods** - API Key, Bearer Token, and Azure AD support
- 🔄 **Automatic Retries** - Built-in retry logic with exponential backoff
- 📦 **Type-Safe** - Full type hints and Pydantic models for all responses
- 📁 **File Upload Support** - Easy dataset creation from CSV, package, and binary files
- 📄 **Pagination Handling** - Automatic pagination for large result sets
- 🚦 **Rate Limiting** - Respects API rate limits with automatic throttling
- ⚡ **Async Support** - Optional async/await support for high-performance applications
- 🧪 **Well-Tested** - Comprehensive test suite with >90% code coverage

## Installation

### Basic Installation

```bash
pip install mindzie-api
```

### With Async Support

```bash
pip install mindzie-api[async]
```

### With Azure AD Authentication

```bash
pip install mindzie-api[azure]
```

### Development Installation

```bash
pip install mindzie-api[dev]
```

## Quick Start

```python
from mindzie_api import MindzieAPIClient

# Initialize the client
client = MindzieAPIClient(
    base_url="https://dev.mindziestudio.com",
    tenant_id="your-tenant-id",
    api_key="your-api-key"
)

# Get all projects
projects = client.projects.get_all()
for project in projects.projects:
    print(f"Project: {project.project_name} (ID: {project.project_id})")

# Get datasets for a project
datasets = client.datasets.get_all(project_id="your-project-id")
print(f"Found {datasets['TotalCount']} datasets")

# Create a dataset from CSV
dataset = client.datasets.create_from_csv(
    project_id="your-project-id",
    dataset_name="Sales Data 2024",
    case_id_column="order_id",
    activity_name_column="activity",
    activity_time_column="timestamp",
    csv_file="path/to/your/data.csv"
)
```

## Configuration

### Environment Variables

The client can be configured using environment variables:

```bash
export MINDZIE_API_URL="https://dev.mindziestudio.com"
export MINDZIE_TENANT_ID="your-tenant-id"
export MINDZIE_API_KEY="your-api-key"
```

Then initialize without parameters:

```python
client = MindzieAPIClient()
```

### Configuration File

Create a `.env` file in your project:

```env
MINDZIE_API_URL=https://dev.mindziestudio.com
MINDZIE_TENANT_ID=your-tenant-id
MINDZIE_API_KEY=your-api-key
```

## Authentication

### API Key Authentication (Default)

```python
client = MindzieAPIClient(
    base_url="https://dev.mindziestudio.com",
    tenant_id="your-tenant-id",
    api_key="your-api-key"
)
```

### Bearer Token Authentication

```python
from mindzie_api import MindzieAPIClient
from mindzie_api.constants import AuthType

client = MindzieAPIClient(
    base_url="https://dev.mindziestudio.com",
    tenant_id="your-tenant-id",
    auth_type=AuthType.BEARER,
    token="your-bearer-token"
)
```

### Azure AD Authentication

```python
from mindzie_api import MindzieAPIClient
from mindzie_api.constants import AuthType

client = MindzieAPIClient(
    base_url="https://dev.mindziestudio.com",
    tenant_id="your-tenant-id",
    auth_type=AuthType.AZURE_AD,
    azure_tenant_id="azure-tenant-id",
    azure_client_id="azure-client-id",
    azure_client_secret="azure-client-secret"
)
```

## API Examples

### Projects

```python
# List all projects
projects = client.projects.get_all(page=1, page_size=50)

# Get project by ID
project = client.projects.get_by_id("project-id")

# Get project summary
summary = client.projects.get_summary("project-id")

# Search projects
results = client.projects.search(
    name_contains="Sales",
    is_active=True,
    min_datasets=5
)
```

### Datasets

```python
# Get all datasets
datasets = client.datasets.get_all("project-id")

# Create dataset from CSV
dataset = client.datasets.create_from_csv(
    project_id="project-id",
    dataset_name="Customer Journey",
    case_id_column="customer_id",
    activity_name_column="action",
    activity_time_column="timestamp",
    csv_file="data.csv",
    resource_column="department",  # Optional
    culture_info="en-US"
)

# Update dataset
updated = client.datasets.update_from_csv(
    project_id="project-id",
    dataset_id="dataset-id",
    case_id_column="customer_id",
    activity_name_column="action",
    activity_time_column="timestamp",
    csv_file="updated_data.csv"
)
```

### Investigations

```python
# Get all investigations
investigations = client.investigations.get_all("project-id")

# Create investigation
investigation = client.investigations.create(
    project_id="project-id",
    name="Q4 Analysis",
    description="Quarterly performance review",
    dataset_id="dataset-id"
)

# Get investigation notebooks
notebooks = client.investigations.get_notebooks(
    project_id="project-id",
    investigation_id="investigation-id"
)
```

### Notebooks

```python
# Get notebook
notebook = client.notebooks.get(
    project_id="project-id",
    notebook_id="notebook-id"
)

# Execute notebook
execution = client.notebooks.execute(
    project_id="project-id",
    notebook_id="notebook-id"
)

# Check execution status
status = client.notebooks.get_execution_status(
    project_id="project-id",
    notebook_id="notebook-id"
)

# Get notebook blocks
blocks = client.notebooks.get_blocks(
    project_id="project-id",
    notebook_id="notebook-id"
)
```

### Blocks

```python
# Get block
block = client.blocks.get(
    project_id="project-id",
    block_id="block-id"
)

# Execute block
result = client.blocks.execute(
    project_id="project-id",
    block_id="block-id"
)

# Create filter block
filter_block = client.blocks.create_filter(
    project_id="project-id",
    name="High Value Orders",
    filter_expression="amount > 1000"
)

# Get block output data
output = client.blocks.get_output_data(
    project_id="project-id",
    block_id="block-id"
)
```

### Dashboards

```python
# Get all dashboards
dashboards = client.dashboards.get_all("project-id")

# Get dashboard panels
panels = client.dashboards.get_panels(
    project_id="project-id",
    dashboard_id="dashboard-id"
)

# Get dashboard URL
url_info = client.dashboards.get_url(
    project_id="project-id",
    dashboard_id="dashboard-id"
)
```

### Execution Queue

```python
# Get execution queue
queue = client.execution.get_queue("project-id")

# Queue notebook execution
execution = client.execution.queue_notebook(
    project_id="project-id",
    notebook_id="notebook-id"
)

# Get execution history
history = client.execution.get_history(
    project_id="project-id",
    page=1,
    page_size=50
)

# Check execution status
status = client.execution.get_status(
    project_id="project-id",
    execution_id="execution-id"
)
```

## Error Handling

```python
from mindzie_api.exceptions import (
    MindzieAPIException,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError
)

try:
    project = client.projects.get_by_id("invalid-id")
except NotFoundError as e:
    print(f"Project not found: {e.message}")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except ServerError as e:
    print(f"Server error: {e.message}")
except MindzieAPIException as e:
    print(f"API error: {e.message}")
```

## Pagination

```python
# Manual pagination
page = 1
while True:
    response = client.projects.get_all(page=page, page_size=100)
    
    for project in response.projects:
        process_project(project)
    
    if not response.has_next:
        break
    
    page = response.next_page

# Automatic pagination (fetches all items)
all_projects = client.projects.list_projects()  # Handles pagination internally
```

## File Uploads

```python
# Upload from file path
dataset = client.datasets.create_from_csv(
    project_id="project-id",
    dataset_name="Sales Data",
    case_id_column="order_id",
    activity_name_column="status",
    activity_time_column="timestamp",
    csv_file="/path/to/data.csv"
)

# Upload from file object
with open("data.csv", "rb") as f:
    dataset = client.datasets.create_from_csv(
        project_id="project-id",
        dataset_name="Sales Data",
        case_id_column="order_id",
        activity_name_column="status",
        activity_time_column="timestamp",
        csv_file=f
    )

# Upload binary data
dataset = client.datasets.create_from_binary(
    project_id="project-id",
    dataset_name="Processed Data",
    binary_file="data.bin"
)
```

## Advanced Configuration

```python
client = MindzieAPIClient(
    base_url="https://dev.mindziestudio.com",
    tenant_id="your-tenant-id",
    api_key="your-api-key",
    timeout=60,  # Request timeout in seconds
    max_retries=5,  # Maximum retry attempts
    verify_ssl=True,  # SSL certificate verification
    proxies={  # Proxy configuration
        "http": "http://proxy.company.com:8080",
        "https": "https://proxy.company.com:8080"
    }
)
```

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=mindzie_api

# Run specific test categories
pytest -m unit
pytest -m integration

# Run tests for specific module
pytest tests/unit/test_project.py
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📧 Email: support@mindzie.com
- 📖 Documentation: [https://docs.mindzie.com/api/python](https://docs.mindzie.com/api/python)
- 🐛 Issues: [GitHub Issues](https://github.com/mindzie/mindzie-api-python/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/mindzie/mindzie-api-python/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes in each version.

## Authors

- **Mindzie Development Team** - *Initial work* - [Mindzie](https://github.com/mindzie)

## Acknowledgments

- Thanks to all contributors who have helped improve this library
- Built with love using Python, Pydantic, and Requests