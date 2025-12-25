# SuperAnnotate Pure Python SDK

A lightweight, pure Python SDK for interacting with the SuperAnnotate platform APIs. This SDK provides a clean, type-safe interface for managing projects, items, annotations, and workflows in SuperAnnotate.

## Features

- **Type-safe**: Built with Pydantic for robust data validation and serialization
- **Async support**: Asynchronous operations for better performance
- **Modular design**: Separate services for different SuperAnnotate components
- **Comprehensive coverage**: Support for items, projects, workflows, annotations, and more
- **Developer-friendly**: Clean API with proper error handling and response models

## Installation

```bash
pip install sa-pure
```


## Services

### Item Service
Manage items (images, videos, documents) in your projects:

```python
from sapure.services.item.api import ItemService

# Get a specific item
item_response = item_service.get(project_id=123, item_id=456)

# List items with filtering
from sapure.services.filters import Query
query = Query()
items_response = item_service.list(
    project_id=123,
    query=query,
    folder_id=789,
    chunk_size=100
)
```


### Auth configuration (Internal/Vault)

When using `auth_type="internal"`, SAInternalAuth (requires the `hvac` package) reads the following environment variables if not explicitly passed:

```bash
export VAULT_ADDR="https://vault.example.com"
export VAULT_ROLE="my-k8s-role"
export KUBERNETES_TOKEN_PATH="/var/run/secrets/kubernetes.io/serviceaccount/token"
export INTERNAL_TOKEN_PATH="kv/data/path/to/internal/token"
```

### Project Management
Work with projects and workflows:

```python
from sapure.services.work_management.api import ProjectsService, WorkflowsService

# Search projects
projects_response = project_service.search(body_query=query)

# List workflow statuses
workflow_service = WorkflowsService(client=client, team_id=123, service_url="https://api.superannotate.com")
statuses = workflow_service.list_statuses(project_id=123, workflow_id=456)
```

### Annotations
Handle annotations and asset management:

```python
from sapure.services.assets_provider.api import AssetsProviderService

# Get annotations for items
asset_service = AssetsProviderService(team_id=123, client=async_client, service_url="https://assets.superannotate.com")
annotations = await asset_service.list_small_annotations(
    project_id=123,
    workflow_id=456,
    project_type="VECTOR",
    classes=[],
    item_ids=[1, 2, 3]
)
```

## Configuration

The SDK uses environment variables for service URLs:

```bash
export ITEM_SERVICE_URL="https://items.superannotate.com"
export SA_BED_URL="https://api.superannotate.com"
```

Or pass them directly to service constructors:

```python
item_service = ItemService(
    team_id=123,
    client=client,
    service_url="https://custom-items.superannotate.com"
)
```

## Response Model

All service methods return a standardized `Response` object:

```python
class Response:
    success: bool
    data: Optional[Union[T, List[T]]]
    errors: Optional[List[ErrorDetail]]

    def first(self) -> Optional[T]:
        """Get first item from list response"""

    def raise_for_status(self):
        """Raise exception if response failed"""
```

## Error Handling

```python
response = item_service.get(project_id=123, item_id=456)

if response.success:
    item = response.data
    print(f"Item: {item.name}")
else:
    print(f"Error: {response.errors[0].message}")

# Or use raise_for_status
try:
    response.raise_for_status()
    item = response.data
except RuntimeError as e:
    print(f"Request failed: {e}")
```

## Supported Entities

- **Items**: Images, videos, documents with metadata and annotations
- **Projects**: Project management and configuration
- **Workflows**: Workflow definitions, statuses, and roles
- **Folders**: Project folder organization
- **Categories**: Item categorization
- **Custom Fields**: Project and item custom metadata
- **Users**: Team member management

## Development

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd sa-pure

# Install development dependencies
pip install -r dev_requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run linting
make linter

# Run type checking
make mypy
```

### Code Quality

The project uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pre-commit** hooks for code quality
- **Pytest** for testing with 80%+ coverage requirement

## Requirements

- Python 3.9+
- httpx ~= 0.28
- pydantic ~= 2.11
- aiofiles ~= 24.1

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Email: support@superannotate.com


Please ensure all tests pass and code coverage remains above 80%.
