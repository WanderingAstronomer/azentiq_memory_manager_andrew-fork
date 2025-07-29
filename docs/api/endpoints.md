# API Endpoints Reference

## Base URL

By default, the API is available at: `http://localhost:8000`

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Common Response Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters or body
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

## Memory CRUD Operations

### Create Memory

**Endpoint:** `POST /memories`

Creates a new memory and stores it in the specified memory tier.

**Request Body:**

```json
{
  "content": "string",
  "metadata": {
    "type": "string",
    "source": "string",
    "session_id": "string",
    "component_id": "string",
    "additional_field": "any"
  },
  "tier": "working",
  "importance": 0.8,
  "ttl": null
}
```

**Response Body:** (201 Created)

```json
{
  "content": "string",
  "metadata": {
    "type": "string",
    "source": "string",
    "session_id": "string",
    "component_id": "string"
  },
  "tier": "working",
  "importance": 0.8,
  "ttl": null,
  "memory_id": "uuid-string",
  "created_at": "2025-07-27T12:21:27.011186",
  "updated_at": "2025-07-27T12:21:27.011200",
  "last_accessed_at": "2025-07-27T12:21:27.011191"
}
```

### Retrieve Memory

**Endpoint:** `GET /memories/{memory_id}`

Retrieves a specific memory by its unique identifier.

**Path Parameters:**

- `memory_id`: UUID of the memory to retrieve

**Response Body:** (200 OK)

```json
{
  "content": "string",
  "metadata": {
    "type": "string",
    "source": "string",
    "session_id": "string",
    "component_id": "string"
  },
  "tier": "working",
  "importance": 0.8,
  "ttl": null,
  "memory_id": "uuid-string",
  "created_at": "2025-07-27T12:21:27.011186",
  "updated_at": "2025-07-27T12:21:27.011200",
  "last_accessed_at": "2025-07-27T12:21:27.011191"
}
```

### Update Memory

**Endpoint:** `PUT /memories/{memory_id}`

Updates an existing memory with new data.

**Path Parameters:**

- `memory_id`: UUID of the memory to update

**Request Body:**

```json
{
  "content": "updated content string",
  "metadata": {
    "type": "updated-type",
    "additional_field": "any"
  },
  "importance": 0.9
}
```

**Response Body:** (200 OK)

```json
{
  "content": "updated content string",
  "metadata": {
    "type": "updated-type",
    "source": "string",
    "session_id": "string",
    "component_id": "string"
  },
  "tier": "working",
  "importance": 0.9,
  "ttl": null,
  "memory_id": "uuid-string",
  "created_at": "2025-07-27T12:21:27.011186",
  "updated_at": "2025-07-28T14:30:45.123456",
  "last_accessed_at": "2025-07-28T14:30:45.123456"
}
```

### Delete Memory

**Endpoint:** `DELETE /memories/{memory_id}`

Removes a memory from storage.

**Path Parameters:**

- `memory_id`: UUID of the memory to delete

**Response Body:** (200 OK)

```json
{
  "detail": "Memory with ID: uuid-string has been deleted"
}
```

### List Memories

**Endpoint:** `GET /memories`

Lists memories with optional filtering by tier and session.

**Query Parameters:**

- `tier` (optional): Filter by memory tier (short_term, working, long_term)
- `session_id` (optional): Filter by session ID
- `skip` (optional, default: 0): Number of memories to skip for pagination
- `limit` (optional, default: 100, max: 1000): Maximum number of memories to return

**Response Body:** (200 OK)

```json
[
  {
    "content": "string",
    "metadata": {
      "type": "string",
      "source": "string",
      "session_id": "string",
      "component_id": "string"
    },
    "tier": "working",
    "importance": 0.8,
    "ttl": null,
    "memory_id": "uuid-string-1",
    "created_at": "2025-07-27T12:21:27.011186",
    "updated_at": "2025-07-27T12:21:27.011200",
    "last_accessed_at": "2025-07-27T12:21:27.011191"
  },
  {
    "content": "another string",
    "metadata": {
      "type": "string",
      "source": "string",
      "session_id": "string",
      "component_id": "string"
    },
    "tier": "working",
    "importance": 0.7,
    "ttl": null,
    "memory_id": "uuid-string-2",
    "created_at": "2025-07-27T12:15:45.123456",
    "updated_at": "2025-07-27T12:15:45.123467",
    "last_accessed_at": "2025-07-27T12:15:45.123461"
  }
]
```

## Conversation Management

### Add Conversation Turn

**Endpoint:** `POST /sessions/{session_id}/turns`

Adds a conversation turn to short-term memory.

**Path Parameters:**

- `session_id`: ID of the session to add the turn to

**Request Body:**

```json
{
  "content": "This is a test message",
  "role": "user",
  "importance": 0.7
}
```

**Response Body:** (200 OK)

```json
{
  "content": "This is a test message",
  "role": "user",
  "importance": 0.7,
  "memory_id": "uuid-string",
  "timestamp": "2025-07-28T18:23:12.861165"
}
```

### Get Recent Turns

**Endpoint:** `GET /sessions/{session_id}/turns`

Retrieves recent conversation history.

**Path Parameters:**

- `session_id`: ID of the session to retrieve turns from

**Query Parameters:**

- `n_turns` (optional, default: 10): Number of turns to retrieve (max: 50)

**Response Body:** (200 OK)

```json
{
  "session_id": "test_session_001",
  "turns": [
    {
      "content": "This is a test message",
      "role": "user",
      "importance": 0.7,
      "memory_id": "uuid-string",
      "timestamp": "2025-07-28T18:23:12.858597"
    }
  ],
  "count": 1
}
```

### Generate Prompt

**Endpoint:** `POST /sessions/{session_id}/prompt`

Creates an optimized prompt with memory context based on token budget.

**Path Parameters:**

- `session_id`: ID of the session to generate a prompt for

**Request Body:**

```json
{
  "system_message": "You are a helpful assistant",
  "user_query": "What did we discuss yesterday?",
  "max_short_term_turns": 5,
  "include_working_memory": true
}
```

**Response Body:** (200 OK)

```json
{
  "prompt": "You are a helpful assistant\n\nRecent conversation history:\n[User]: What's the weather like?\n[Assistant]: It's sunny today.\n\nRelevant memories:\n- We discussed project deadlines yesterday\n- The user mentioned they have a meeting next week\n\n[User]: What did we discuss yesterday?",
  "token_usage": 82
}
```

## Session & Context Management

### Set Context

**Endpoint:** `POST /context`

Sets component and session context for memory operations.

**Request Body:**

```json
{
  "session_id": "string",
  "component_id": "string"
}
```

**Response Body:** (200 OK)

```json
{
  "session_id": "string",
  "component_id": "string"
}
```

### Get Session Context

**Endpoint:** `GET /sessions/{session_id}/context`

Retrieves all context key-value pairs for a session.

**Path Parameters:**

- `session_id`: ID of the session to retrieve context for

**Response Body:** (200 OK)

```json
{
  "session_id": "string",
  "context": {
    "last_topic": "weather",
    "user_preference": "concise",
    "timezone": "America/New_York"
  }
}
```

### Store Context Value

**Endpoint:** `PUT /sessions/{session_id}/context/{key}`

Stores/updates a single context value.

**Path Parameters:**

- `session_id`: ID of the session to update context for
- `key`: Context key to store/update

**Request Body:**

```json
"context value string or object"
```

**Response Body:** (200 OK)

```json
{
  "key": "string",
  "value": "context value string or object",
  "session_id": "string"
}
```

## System Management

### Health Check

**Endpoint:** `GET /health`

Standard endpoint for monitoring service health.

**Response Body:** (200 OK)

```json
{
  "status": "healthy",
  "components": {
    "redis": "connected",
    "vector_store": "connected"
  },
  "uptime_seconds": 3600
}
```

### Version Info

**Endpoint:** `GET /version`

Provides API version information for clients.

**Response Body:** (200 OK)

```json
{
  "version": "1.0.0",
  "build_date": "2025-07-01",
  "api_spec": "v1"
}
```
