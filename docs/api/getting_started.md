# Getting Started with the Memory Manager API

This guide will help you get started with using the Azentiq Memory Manager API.

## Prerequisites

- Python 3.8 or higher
- Redis server running (default: localhost:6379)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/azentiq/memory-manager.git
   cd azentiq_memory_manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Starting the API Server

### Using the Batch File (Windows)

The simplest way to start the API server on Windows is to use the provided batch file:

```bash
# Start the API service
run_api_service.bat
```

### Manual Start

Alternatively, you can start the service manually:

```bash
# Using the run script
python -m services.run_api --reload

# Or directly with uvicorn
uvicorn services.api.main:app --reload
```

The API will be accessible at http://localhost:8000 with interactive documentation available at http://localhost:8000/docs.

## Basic Usage Examples

### Create a Memory

```python
import requests
import json

api_url = "http://localhost:8000"

# Create a memory
memory_data = {
    "content": "User prefers dark mode in all applications",
    "metadata": {
        "type": "preference",
        "source": "user_settings",
        "session_id": "user_session_001",
        "component_id": "settings_module"
    },
    "tier": "working",
    "importance": 0.8
}

response = requests.post(
    f"{api_url}/memories",
    json=memory_data
)

if response.status_code == 201:
    memory = response.json()
    memory_id = memory["memory_id"]
    print(f"Memory created with ID: {memory_id}")
else:
    print(f"Failed to create memory: {response.text}")
```

### Retrieve a Memory

```python
import requests

api_url = "http://localhost:8000"
memory_id = "your-memory-id"  # Replace with an actual memory ID

response = requests.get(f"{api_url}/memories/{memory_id}")

if response.status_code == 200:
    memory = response.json()
    print(f"Memory content: {memory['content']}")
    print(f"Created at: {memory['created_at']}")
else:
    print(f"Failed to retrieve memory: {response.text}")
```

### Add a Conversation Turn

```python
import requests

api_url = "http://localhost:8000"
session_id = "user_session_001"

turn_data = {
    "content": "What's the weather like today?",
    "role": "user",
    "importance": 0.7
}

response = requests.post(
    f"{api_url}/sessions/{session_id}/turns",
    json=turn_data
)

if response.status_code == 200:
    turn = response.json()
    print(f"Turn added with ID: {turn['memory_id']}")
else:
    print(f"Failed to add turn: {response.text}")
```

### Generate a Prompt with Memory Context

```python
import requests

api_url = "http://localhost:8000"
session_id = "user_session_001"

prompt_request = {
    "system_message": "You are a helpful assistant.",
    "user_query": "What were my preferences again?",
    "max_short_term_turns": 5,
    "include_working_memory": True
}

response = requests.post(
    f"{api_url}/sessions/{session_id}/prompt",
    json=prompt_request
)

if response.status_code == 200:
    result = response.json()
    print(f"Generated prompt: {result['prompt']}")
    print(f"Token usage: {result['token_usage']}")
else:
    print(f"Failed to generate prompt: {response.text}")
```

## Common Patterns

### Error Handling

Always check response status codes and handle errors appropriately:

```python
response = requests.get(f"{api_url}/memories/{memory_id}")

if response.status_code == 200:
    # Process successful response
    memory = response.json()
elif response.status_code == 404:
    print(f"Memory {memory_id} not found")
elif response.status_code == 500:
    print(f"Server error: {response.text}")
else:
    print(f"Unexpected error: {response.status_code} - {response.text}")
```

### Session Management

For consistent memory retrieval, always use the same session_id and component_id when storing and retrieving memories:

```python
# Define consistent context parameters
session_id = "user_session_001"
component_id = "my_component"

# Include in metadata when creating memories
memory_data = {
    "content": "Some content",
    "metadata": {
        "session_id": session_id,
        "component_id": component_id,
        # Other metadata...
    },
    # Other memory attributes...
}
```

## Troubleshooting

### Memory Not Found After Creation

If memories are created successfully but can't be retrieved, check:

1. The context parameters match between creation and retrieval (component_id, session_id)
2. The memory is being created in the expected tier

### Redis Connection Issues

Ensure Redis is running on the configured URL (default: `redis://localhost:6379/0`). You can modify this by setting the `REDIS_URL` environment variable.

## Next Steps

- Explore the full [API Reference](endpoints.md)
- Review [Request/Response Schemas](schemas.md)
- Check out [Common Use Cases](use_cases.md)
