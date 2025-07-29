# Memory CRUD Operations Sequence Diagrams

This document illustrates the sequence flows for memory CRUD (Create, Read, Update, Delete) operations in the Azentiq Memory Manager API.

## Create Memory Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: POST /memories
    Note over C,API: JSON payload with content, metadata, tier, importance
    
    API->>MM: add_memory(content, metadata, tier, importance)
    MM->>MM: Create Memory object
    MM->>MM: Generate UUID memory_id
    MM->>RS: store_memory(memory, namespace)
    Note over MM,RS: Namespace includes tier, session_id, component_id
    
    RS-->>MM: Return success
    MM-->>API: Return memory_id
    
    API->>MM: get_memory(memory_id)
    MM->>RS: get_memory(memory_id, namespace)
    RS-->>MM: Return stored memory
    MM-->>API: Return Memory object
    
    API-->>C: 201 Created (Memory object as JSON)
```

## Read Memory Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: GET /memories/{memory_id}
    
    API->>MM: get_memory(memory_id)
    
    alt Direct memory lookup
        MM->>RS: get_memory(memory_id, namespace)
        RS-->>MM: Return stored memory if found
    else Try tier-by-tier fallback
        MM->>RS: get_memory(memory_id, working_namespace)
        RS-->>MM: Not found
        MM->>RS: get_memory(memory_id, short_term_namespace)
        RS-->>MM: Not found
        MM->>RS: get_memory(memory_id, long_term_namespace)
        RS-->>MM: Memory found
    end
    
    alt Memory found
        MM-->>API: Return Memory object
        API-->>C: 200 OK (Memory object as JSON)
    else Memory not found
        MM-->>API: Return None
        API-->>C: 404 Not Found
    end
```

## Update Memory Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: PUT /memories/{memory_id}
    Note over C,API: JSON payload with updated fields
    
    API->>MM: get_memory(memory_id)
    MM->>RS: get_memory(memory_id, namespace)
    
    alt Memory exists
        RS-->>MM: Return stored memory
        MM-->>API: Return Memory object
        
        API->>API: Update Memory with new fields
        API->>MM: add_memory(updated_memory)
        MM->>RS: store_memory(updated_memory, namespace)
        RS-->>MM: Return success
        MM-->>API: Return memory_id
        
        API-->>C: 200 OK (Updated Memory object as JSON)
    else Memory not found
        RS-->>MM: Memory not found
        MM-->>API: Return None
        API-->>C: 404 Not Found
    end
```

## Delete Memory Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: DELETE /memories/{memory_id}
    
    API->>MM: get_memory(memory_id)
    MM->>RS: get_memory(memory_id, namespace)
    
    alt Memory exists
        RS-->>MM: Return stored memory
        MM-->>API: Return Memory object
        
        API->>MM: delete_memory(memory_id)
        MM->>RS: delete_memory(memory_id, namespace)
        RS-->>MM: Return success
        MM-->>API: Return success
        
        API-->>C: 200 OK (Deletion confirmation message)
    else Memory not found
        RS-->>MM: Memory not found
        MM-->>API: Return None
        API-->>C: 404 Not Found
    end
```

## List Memories Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: GET /memories
    Note over C,API: Optional query params: tier, session_id, skip, limit
    
    API->>MM: list_memories(tier, session_id, skip, limit)
    MM->>RS: list_memories(namespace, skip, limit)
    Note over MM,RS: Namespace constructed from tier, session_id, component_id
    
    RS-->>MM: Return memory_ids array
    
    loop For each memory_id
        MM->>RS: get_memory(memory_id, namespace)
        RS-->>MM: Return memory object
    end
    
    MM-->>API: Return array of Memory objects
    API-->>C: 200 OK (Array of Memory objects as JSON)
```

## Key Implementation Details

### Namespace Construction

The namespace used for Redis key generation is critical for proper memory storage and retrieval:

```
memory:{tier}:{session_id}:{component_id}:{memory_id}
```

For example:
```
memory:working:default:main:04c169ca-2a45-44b3-9338-63fada870dad
```

### Memory Storage Types

- **Short-term memory**: Recent conversation turns and ephemeral context
- **Working memory**: Important facts, preferences, and session state
- **Long-term memory**: Persistent knowledge and information

### Error Handling

- If Redis connectivity fails, a 500 Internal Server Error is returned
- If a memory is not found during read/update/delete, a 404 Not Found is returned
- If invalid parameters are provided, a 400 Bad Request is returned
