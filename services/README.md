# Azentiq Memory Manager API Service

This directory contains the FastAPI implementation for exposing the Azentiq Memory Manager's core functionality as RESTful APIs.

> **Status:** All API endpoints are fully functional and tested.

## Overview

The Memory Manager API Service provides HTTP endpoints to interact with the Memory Manager's key features:

- Memory CRUD operations (create, read, update, delete)
- Memory listing and searching
- Session and context management
- Conversation history management
- Prompt generation with memory integration

## API Endpoints

### Memory CRUD Operations

- **Create Memory**
  - `POST /memories`
  - Creates a new memory in the specified tier

- **Retrieve Memory**
  - `GET /memories/{memory_id}`
  - Retrieves a specific memory by ID

- **Update Memory**
  - `PUT /memories/{memory_id}`
  - Updates an existing memory's content, metadata, or other attributes

- **Delete Memory**
  - `DELETE /memories/{memory_id}`
  - Removes a memory from storage

### Memory Listing & Search

- **List Memories**
  - `GET /memories`
  - Lists memories with pagination and optional filtering by tier/session

- **Search by Metadata**
  - `POST /memories/search`
  - Searches for memories matching metadata criteria

### Session & Context Management

- **Set Context**
  - `POST /context`
  - Sets component and session context for memory operations

- **Get Session Context**
  - `GET /sessions/{session_id}/context`
  - Retrieves all context key-value pairs for a session

- **Store Context Value**
  - `PUT /sessions/{session_id}/context/{key}`
  - Stores/updates a single context value

### Conversation Management

- **Add Conversation Turn**
  - `POST /sessions/{session_id}/turns`
  - Adds a conversation turn to short-term memory

- **Get Recent Turns**
  - `GET /sessions/{session_id}/turns`
  - Retrieves recent conversation history

- **Generate Prompt**
  - `POST /sessions/{session_id}/prompt`
  - Creates an optimized prompt with memory context based on token budget

### System Management

- **Health Check**
  - `GET /health`
  - Standard endpoint for monitoring service health

- **Version Info**
  - `GET /version`
  - Provides API version information for clients

## Implementation Structure

The service layer is organized as follows:

- `api/` - API route definitions and handlers
- `schemas/` - Pydantic models for request/response validation
- `dependencies/` - FastAPI dependencies (authentication, memory manager instance)
- `middleware/` - Custom middleware for request processing

## Usage

### Using the Batch File (Windows)

A batch file is provided in the root directory for easy service management:

```batch
# Start the API service
run_api_service.bat

# Run tests against the API
run_api_service.bat test

# Install required dependencies
run_api_service.bat install
```

### Manual Start

Alternatively, you can start the service manually:

```bash
# Using the run script
python -m services.run_api --reload

# Or directly with uvicorn
uvicorn services.api.main:app --reload
```

### Testing the API

To test the API endpoints:

```bash
python -m services.test_api
```

The API will be accessible at http://localhost:8000 with interactive documentation available at http://localhost:8000/docs.

## Troubleshooting

### Import Errors

If you encounter module import errors when starting the API service, the most common issues are:

1. **Python Path Issues**: The project uses a `pythonpath_helper.py` to ensure the project root is in the Python path. This is automatically used by the run scripts.

2. **Import Path Corrections**: Core classes are imported from their correct locations:
   - `Memory` and `MemoryTier` classes are defined in `core.interfaces`, not `core.memory`
   - The Memory Manager is imported from `core.memory_manager`

### Redis Connection

Ensure Redis is running on the configured URL (default: `redis://localhost:6379/0`). You can modify this by setting the `REDIS_URL` environment variable.

### Memory Not Found After Creation

If memories are created successfully but can't be retrieved, check:

1. The context parameters match between creation and retrieval (component_id, session_id)
2. The memory is being created in the expected tier

The API uses consistent context parameters by default (`component_id='main'`, `session_id='default'`) in the memory manager dependency.
