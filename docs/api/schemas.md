# API Request and Response Schemas

This document details the data models used for requests and responses in the Azentiq Memory Manager API.

## Memory Models

### Memory Request Schema

Used when creating or updating memories.

```python
class MemoryRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    tier: Optional[MemoryTier] = MemoryTier.WORKING
    importance: Optional[float] = 0.5
    ttl: Optional[int] = None
```

### Memory Response Schema

Returned when retrieving memories or after creating/updating them.

```python
class MemoryResponse(BaseModel):
    content: str
    metadata: Dict[str, Any]
    tier: MemoryTier
    importance: float
    ttl: Optional[int]
    memory_id: str
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime
```

## Session and Context Models

### Context Request Schema

Used when setting component and session context.

```python
class ContextRequest(BaseModel):
    session_id: str
    component_id: str
```

### Session Context Response Schema

Returned when retrieving all context for a session.

```python
class SessionContextResponse(BaseModel):
    session_id: str
    context: Dict[str, Any]
```

## Conversation Models

### Conversation Turn Request Schema

Used when adding a new conversation turn.

```python
class ConversationTurn(BaseModel):
    content: str
    role: str  # "user", "assistant", or "system"
    importance: float = 0.5
```

### Conversation Turn Response Schema

Returned after adding a conversation turn.

```python
class ConversationTurnResponse(BaseModel):
    content: str
    role: str
    importance: float
    memory_id: str
    timestamp: datetime
```

### Conversation History Response Schema

Returned when retrieving conversation history.

```python
class ConversationHistory(BaseModel):
    session_id: str
    turns: List[ConversationTurnResponse]
    count: int
```

## Prompt Generation Models

### Prompt Request Schema

Used when generating a prompt with memory integration.

```python
class PromptRequest(BaseModel):
    system_message: str
    user_query: str
    max_short_term_turns: int = 5
    include_working_memory: bool = True
```

### Prompt Response Schema

Returned after generating a prompt.

```python
class PromptResponse(BaseModel):
    prompt: str
    token_usage: int
```

## System Models

### Health Response Schema

Returned from the health check endpoint.

```python
class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    uptime_seconds: int
```

### Version Response Schema

Returned from the version info endpoint.

```python
class VersionResponse(BaseModel):
    version: str
    build_date: str
    api_spec: str
```

## Metadata Structures

### Common Metadata Fields

These fields are commonly used in memory metadata:

```python
{
    "type": str,  # Type of memory (e.g., "fact", "preference", "conversation_turn")
    "source": str,  # Source of the memory (e.g., "user", "system", "api_call")
    "session_id": str,  # Session identifier
    "component_id": str,  # Component identifier
    "timestamp": str,  # ISO format timestamp when memory was created
    # Additional custom fields can be added as needed
}
```

## Enumeration Types

### Memory Tier

```python
class MemoryTier(str, Enum):
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"
```

## Response Format Consistency

All success responses follow consistent patterns:
- Single resource operations (create, read, update) return the resource object
- List operations return arrays of resource objects
- Delete operations return confirmation messages

All error responses follow this pattern:
```json
{
    "detail": "Error description message"
}
```
