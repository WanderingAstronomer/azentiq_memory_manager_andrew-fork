# Conversation Management Sequence Diagrams

This document illustrates the sequence flows for conversation management operations in the Azentiq Memory Manager API.

## Add Conversation Turn Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: POST /sessions/{session_id}/turns
    Note over C,API: JSON payload with content, role, importance
    
    API->>MM: add_conversation_turn(session_id, content, role, importance)
    Note over MM: Creates memory in short_term tier
    
    MM->>MM: Create Memory object
    Note over MM: Set metadata with role, timestamp
    MM->>MM: Generate UUID memory_id
    
    MM->>RS: store_memory(memory, namespace)
    Note over MM,RS: Namespace: memory:short_term:{session_id}:{component_id}:{memory_id}
    
    RS-->>MM: Return success
    MM-->>API: Return memory_id
    
    API->>MM: get_memory(memory_id)
    MM->>RS: get_memory(memory_id, namespace)
    RS-->>MM: Return stored memory
    MM-->>API: Return Memory object
    
    API-->>C: 200 OK (ConversationTurnResponse as JSON)
```

## Get Recent Turns Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: GET /sessions/{session_id}/turns
    Note over C,API: Optional query param: n_turns (default: 10)
    
    API->>MM: get_recent_turns(session_id, n_turns)
    
    MM->>RS: list_memory_keys_by_recency(short_term_namespace)
    Note over MM,RS: Namespace: memory:short_term:{session_id}:*
    
    RS-->>MM: Return memory_keys array (sorted by timestamp)
    
    loop For each key (limited by n_turns)
        MM->>RS: get_memory(memory_id, namespace)
        RS-->>MM: Return memory object
    end
    
    MM-->>API: Return array of Memory objects
    
    loop For each memory
        API->>API: Convert Memory to ConversationTurnResponse
    end
    
    API-->>C: 200 OK (ConversationHistory with turns array)
```

## Generate Prompt Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Endpoint
    participant MM as Memory Manager
    participant RS as Redis Store
    
    C->>API: POST /sessions/{session_id}/prompt
    Note over C,API: JSON payload with system_message, user_query, options
    
    API->>MM: generate_prompt(session_id, system_message, user_query, options)
    
    MM->>MM: get_recent_turns(session_id, max_short_term_turns)
    MM->>RS: list_memory_keys_by_recency(short_term_namespace)
    RS-->>MM: Return memory_keys array
    
    loop For each key (limited by max_short_term_turns)
        MM->>RS: get_memory(memory_id, namespace)
        RS-->>MM: Return memory object
        MM->>MM: Format turn for prompt
    end
    
    alt Include working memory is true
        MM->>RS: list_memory_keys_by_importance(working_namespace)
        Note over MM,RS: Namespace: memory:working:{session_id}:*
        RS-->>MM: Return memory_keys array (sorted by importance)
        
        loop For each key (limited by token budget)
            MM->>RS: get_memory(memory_id, namespace)
            RS-->>MM: Return memory object
            MM->>MM: Format memory for prompt
        end
    end
    
    MM->>MM: Assemble prompt with system_message + turns + memories + user_query
    MM->>MM: Calculate token usage
    
    MM-->>API: Return prompt text and token usage
    API-->>C: 200 OK (PromptResponse with prompt and token_usage)
```

## Key Implementation Details

### Conversation Turn Storage

Conversation turns are stored as Memory objects in the short_term tier with special metadata:

```json
{
  "content": "This is a message",
  "metadata": {
    "type": "conversation_turn",
    "role": "user", // or "assistant", "system"
    "timestamp": "2025-07-28T18:23:12.858597",
    "session_id": "session_id",
    "component_id": "component_id"
  },
  "tier": "short_term",
  "importance": 0.7,
  "ttl": 86400, // optional TTL in seconds
  "memory_id": "uuid-string"
}
```

### Prompt Construction

The Memory Manager constructs prompts using this general template:

```
{system_message}

Recent conversation history:
{turn 1 role}: {turn 1 content}
{turn 2 role}: {turn 2 content}
...

Relevant memories:
- {memory 1 content}
- {memory 2 content}
...

{user role}: {user_query}
```

### Memory Ranking for Prompt Integration

For working memory integration in prompts, memories are selected based on:

1. Importance score (higher scores are prioritized)
2. Recency (newer memories are prioritized)
3. Token budget constraints (to prevent exceeding model context windows)

This ensures the most relevant context is included in the prompt.
