# CRF API Client

Python SDK for the Clarifeye Platform API.

## Documentation

| Document | Description |
|----------|-------------|
| [OVERVIEW.md](./OVERVIEW.md) | Architecture and component overview |
| [AGENTS.md](./AGENTS.md) | AI assistant guidance |

## Installation

```bash
pip install crf-api-client

# Or from source
pip install -e .
```

## Quick Start

```python
from crf_api_client import CRFAPIClient

# Initialize client
client = CRFAPIClient(
    base_url="https://your-instance.clarifeye.io",
    token="your-api-token"
)

# List warehouses
warehouses = client.list_warehouses()
for wh in warehouses:
    print(f"{wh.name}: {wh.id}")

# Get a specific warehouse
warehouse = client.get_warehouse("warehouse-uuid")

# Create a new warehouse
new_warehouse = client.create_warehouse(
    name="My Warehouse",
    brief="A warehouse for my documents"
)
```

## Key Features

### Warehouse Management

```python
# List all warehouses
warehouses = client.list_warehouses()

# Create warehouse
warehouse = client.create_warehouse(name="My Warehouse")

# Get warehouse
warehouse = client.get_warehouse("warehouse-id")

# Delete warehouse
client.delete_warehouse("warehouse-id")
```

### Document Operations

```python
# Upload document
doc = warehouse.upload_document("path/to/document.pdf")

# List documents
documents = warehouse.list_documents()

# Get document
document = warehouse.get_document("document-id")
```

### Pipeline Execution

```python
# Run parsing pipeline
task = warehouse.run_parsing_task(document_ids=["doc-id"])

# Monitor task
task.wait_for_completion()
print(task.status)
```

### AI Assistants

```python
# Create playground agent
agent = warehouse.get_playground_agent()

# Chat with agent
response = agent.chat("What documents do you have?")
print(response)
```

### Export/Import

```python
# Export warehouse
warehouse.export_to_file("warehouse_backup.zip")

# Import warehouse
client.import_warehouse("warehouse_backup.zip")
```

## Authentication

Get your API token from the Clarifeye Platform:
1. Log in to the web interface
2. Go to `/api/v1/get-token/`
3. Copy your token

## Project Structure

```
crf_api_client/
├── crf_api_client/
│   ├── __init__.py
│   ├── client.py           # Main CRFAPIClient class
│   ├── warehouse.py        # Warehouse class
│   ├── table.py            # Table operations
│   ├── task.py             # Task monitoring
│   ├── base.py             # Base API client
│   ├── models.py           # Pydantic models
│   ├── exception.py        # Custom exceptions
│   ├── playground_agent.py # AI playground agent
│   ├── knowledge_assistant.py
│   ├── react_assistant.py
│   └── operations/
│       ├── client_operations.py
│       └── warehouse_operations.py
├── tests/                  # Test suite
├── pyproject.toml          # Package configuration
└── requirements.txt        # Dependencies
```

## Development

### Setup

```bash
cd crf_api_client
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Code Quality

```bash
ruff check crf_api_client/
ruff format crf_api_client/
```

## Requirements

- Python 3.11+
- requests
- pydantic
- llama-index (for RAG features)
- openai (for assistant features)

