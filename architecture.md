# Azentiq Memory Manager Architecture

## Overview

Azentiq Memory Manager is a Python 3.11+ library that provides memory management capabilities for AI applications. The core focus is on maintaining different tiers of memories with efficient storage, retrieval, and token budget management. The MVP implementation focuses on session memory via Redis with a CLI demo.

## System Architecture

```mermaid
graph TD
    %% Client Applications
    Client[Client Application] --> |API Calls| MM[Memory Manager]
    CLI[CLI Tool] --> |Commands| MM
    
    %% Core Memory Manager
    subgraph "Core System"
        MM --> |Store/Retrieve| RS[Redis Store]
        MM --> |Token Management| TBM[Token Budget Manager]
        MM --> |Manages| MT[Memory Tiers]
    end
    
    %% Memory Tiers
    subgraph "Memory Tiers"
        MT --> STM[Short-Term Memory]
        MT --> WM[Working Memory]
        MT --> LTM[Long-Term Memory]
    end
    
    %% Storage System
    subgraph "Storage Layer"
        RS --> |Namespaced Keys| RDB[(Redis Database)]
        RS --> |Uses| NS[Namespace Handler]
        NS --> |Format| NSP["tier:session:framework:component:id"]
    end
    
    %% Token Budget System
    subgraph "Token Budgeting System"
        TBM --> TE[Token Estimator]
        TBM --> MS[Memory Selector]
        TBM --> AS[Adaptation Strategies]
        TBM --> PC[Prompt Construction]
        
        MS --> PMS[Priority Memory Selector]
        MS --> RMS[Relevance Memory Selector]
        
        AS --> RAS[Reduce Adaptation]
        AS --> SAS[Summarize Adaptation]
        AS --> PTS[Prioritize Tier Strategy]
        
        PC --> MF[Memory Formatter]
        PC --> PCN[Prompt Constructor]
    end
    
    %% Framework Adapters
    subgraph "Framework Adapters"
        MM --> |Future| LCA[LangChain Adapter]
        MM --> |Future| LGA[LangGraph Adapter]
    end
    
    %% Data Flow for Memory Operations
    Client --> |1. Add Memory| MM
    MM --> |2. Create Namespace| NS
    MM --> |3. Store With TTL| RS
    RS --> |4. Persist| RDB
    
    Client --> |1. Retrieve Memories| MM
    MM --> |2. Request By Namespace| NS
    NS --> |3. Build Key| RS
    RS --> |4. Fetch From DB| RDB
    RS --> |5. Return Memory| MM
    
    Client --> |1. Generate Prompt| MM
    MM --> |2. Fetch Memories| RS
    MM --> |3. Estimate Tokens| TE
    MM --> |4. Select Memories| MS
    MM --> |5. Apply Adaptation| AS
    MM --> |6. Format Memories| MF
    MM --> |7. Construct Prompt| PCN
    MM --> |8. Return Prompt| Client

    %% Styling
    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    classDef storage fill:#bbf,stroke:#333,stroke-width:1px;
    classDef token fill:#bfb,stroke:#333,stroke-width:1px;
    classDef tier fill:#ffb,stroke:#333,stroke-width:1px;
    classDef adapter fill:#fbb,stroke:#333,stroke-width:1px;
    
    class MM,MT core;
    class RS,RDB,NS storage;
    class TBM,TE,MS,AS,PC,PMS,RMS,RAS,SAS,PTS,MF,PCN token;
    class STM,WM,LTM tier;
    class LCA,LGA adapter;
```

## Component Relationships

```mermaid
classDiagram
    class MemoryManager {
        +RedisStore redis_store
        +TokenBudgetManager token_budget_manager
        +set_context(component_id)
        +add_memory(content, metadata, tier)
        +get_memory(memory_id, tier)
        +list_memories(tier, session_id)
        +search_by_metadata(query, tier)
        +generate_prompt(session_id, query)
    }
    
    class Memory {
        +String memory_id
        +String content
        +Dict metadata
        +Float importance
        +MemoryTier tier
        +DateTime created_at
        +DateTime last_accessed_at
    }
    
    class MemoryTier {
        <<enumeration>>
        SHORT_TERM
        WORKING
        LONG_TERM
    }
    
    class RedisStore {
        +set_context(component_id)
        +add(memory, session_id)
        +get(memory_id, tier_str, session_id)
        +update(memory, session_id)
        +delete(memory_id, tier_str, session_id)
        +list(tier_str, session_id)
        +search_by_metadata(query, limit, tier_str)
    }
    
    class TokenBudgetManager {
        +TokenEstimator estimator
        +MemorySelector selector
        +Set~AdaptationStrategy~ strategies
        +PromptConstructor prompt_constructor
        +set_context(component_id, session_id)
        +estimate_tokens(text)
        +select_memories(memories, max_tokens)
        +construct_prompt_with_memories(...)
    }
    
    class TokenEstimator {
        +estimate_tokens(text)
        +estimate_memory_tokens(memory)
        +estimate_memories_tokens(memories)
    }
    
    class MemorySelector {
        <<interface>>
        +select_memories(memories, max_tokens)
    }
    
    class PriorityMemorySelector {
        +select_memories(memories, max_tokens)
    }
    
    class RelevanceMemorySelector {
        +select_memories(memories, max_tokens)
    }
    
    class AdaptationStrategy {
        <<interface>>
        +adapt_memories(memories, target_tokens)
    }
    
    class ReduceAdaptationStrategy {
        +adapt_memories(memories, target_tokens)
    }
    
    class SummarizeAdaptationStrategy {
        +adapt_memories(memories, target_tokens)
    }
    
    class PrioritizeTierStrategy {
        +adapt_memories(memories, target_tokens)
    }
    
    class MemoryFormatter {
        +format_memory(memory, index)
        +format_memories(memories, section_title)
    }
    
    class PromptConstructor {
        +TokenEstimator token_estimator
        +construct_prompt(user_input, memory_sections)
    }
    
    MemoryManager *-- RedisStore : uses
    MemoryManager *-- TokenBudgetManager : uses
    MemoryManager --> Memory : manages
    MemoryManager --> MemoryTier : uses
    
    TokenBudgetManager *-- TokenEstimator : uses
    TokenBudgetManager *-- MemorySelector : uses
    TokenBudgetManager *-- AdaptationStrategy : uses
    TokenBudgetManager *-- PromptConstructor : uses
    
    Memory --> MemoryTier : has
    
    MemorySelector <|.. PriorityMemorySelector : implements
    MemorySelector <|.. RelevanceMemorySelector : implements
    
    AdaptationStrategy <|.. ReduceAdaptationStrategy : implements
    AdaptationStrategy <|.. SummarizeAdaptationStrategy : implements
    AdaptationStrategy <|.. PrioritizeTierStrategy : implements
    
    PromptConstructor *-- MemoryFormatter : uses
    PromptConstructor *-- TokenEstimator : uses
```

## Memory Namespacing

```mermaid
graph TD
    subgraph "Namespace Structure"
        NS["{tier}:{session_id}:{framework}:{component_id}:{memory_id}"]
    end
    
    subgraph "Example Namespaces"
        NS1["short_term:session123:app:main:550e8400-e29b-41d4-a716-446655440000"]
        NS2["working:session123:langchain:planner:550e8400-e29b-41d4-a716-446655440000"]
        NS3["working:session456:langgraph:executor:550e8400-e29b-41d4-a716-446655440000"]
    end
    
    subgraph "Framework Isolation"
        F1[App Framework]
        F2[LangChain Framework]
        F3[LangGraph Framework]
    end
    
    subgraph "Component Isolation"
        C1[Main Component]
        C2[Planner Component]
        C3[Executor Component]
    end
    
    F1 --- NS1
    F2 --- NS2
    F3 --- NS3
    
    C1 --- NS1
    C2 --- NS2
    C3 --- NS3
    
    NS1 --- RDB[(Redis DB)]
    NS2 --- RDB
    NS3 --- RDB
```

## Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant MM as Memory Manager
    participant RS as Redis Store
    participant NS as Namespace Handler
    participant RDB as Redis DB
    participant TBM as Token Budget Manager
    
    %% Memory Creation Flow
    Client->>MM: add_memory(content, tier, session_id)
    MM->>RS: add(memory, session_id)
    RS->>NS: _get_namespace(memory_id, tier, session_id)
    NS-->>RS: namespaced_key
    RS->>RDB: store(namespaced_key, memory)
    
    %% Memory Retrieval Flow
    Client->>MM: get_memory(memory_id, tier, session_id)
    MM->>RS: get(memory_id, tier_str, session_id)
    RS->>NS: _get_namespace(memory_id, tier, session_id)
    NS-->>RS: namespaced_key
    RS->>RDB: fetch(namespaced_key)
    RDB-->>RS: serialized_memory
    RS-->>MM: deserialized_memory
    MM-->>Client: memory
    
    %% Prompt Generation Flow
    Client->>MM: generate_prompt(session_id, query)
    MM->>RS: list(tier_str, session_id)
    RS->>RDB: scan(namespace_pattern)
    RDB-->>RS: matching_keys
    RS->>RDB: mget(matching_keys)
    RDB-->>RS: serialized_memories
    RS-->>MM: deserialized_memories
    MM->>TBM: construct_prompt_with_memories(query, memories)
    TBM-->>MM: formatted_prompt
    MM-->>Client: prompt
```

## Implementation Guidelines

### MVP Focus

The initial implementation (MVP) focuses on:

1. **Single Memory Tier**: Implement session memory via Redis
2. **CLI Demo**: Create a command-line interface for demonstrating core functionality
3. **Core API**: Implement the essential memory operations (add, get, list, search)
4. **Prompt Construction**: Include basic token management and prompt construction

### Storage Implementation

The Redis storage implementation will use the following approach:

- **Session-based Storage**: All memories are stored with session identifiers
- **Namespacing**: Keys follow the pattern `{tier}:{session_id}:{framework}:{component_id}:{memory_id}`
- **TTL Management**: Different memory tiers have different Time-To-Live values
  - Short-term: 1 hour
  - Working: 1 day
  - Long-term: 30 days (configurable)

### Token Budget Management

Token budget management is critical for effective prompt construction:

1. **Token Estimation**: Uses a configurable estimator for accurate token counting
2. **Memory Selection**: Prioritizes memories based on importance and recency
3. **Adaptation Strategies**: Implements methods to fit within token constraints
4. **Format Templates**: Supports customizable templates for memory formatting

### API Design

The API is designed to be intuitive and flexible:

```python
# Initialize memory manager
manager = MemoryManager(redis_url="redis://localhost:6379/0")

# Set context for component
manager.set_context(component_id="my_component")

# Add memory
memory_id = manager.add_memory(
    content="Important information to remember",
    metadata={"importance": 0.9, "category": "user_preference"},
    tier=MemoryTier.WORKING,
    session_id="user_session_123"
)

# Retrieve memory
memory = manager.get_memory(
    memory_id=memory_id,
    tier=MemoryTier.WORKING,
    session_id="user_session_123"
)

# Generate prompt with memories
prompt = manager.generate_prompt(
    session_id="user_session_123",
    query="What do you remember about my preferences?",
    system_message="You are an assistant with memory capabilities."
)
```

## Technology Stack

- **Python 3.11+**: Required for all development and usage
- **Redis**: Primary storage for session memory tier
- **Packaging**: Standard Python packaging with pyproject.toml
- **Testing**: Comprehensive unit tests with pytest

## Extension Points

The architecture supports future extensions:

1. **Framework Adapters**: LangChain and LangGraph adapters
2. **Additional Memory Tiers**: Support for more specialized memory types
3. **Vector Storage**: Integration with vector databases for semantic search
4. **Advanced Selection**: Enhanced selection algorithms based on relevance

## Future Roadmap

After the MVP release, planned enhancements include:

1. **LangChain Adapter**: Integration with LangChain ecosystem
2. **LangGraph Adapter**: Integration with LangGraph for stateful workflows
3. **Vector Store Integration**: Add support for semantic search and retrieval
4. **Improved Selection**: More sophisticated memory selection algorithms
5. **Memory Analytics**: Tools for analyzing memory usage and patterns

## Testing Strategy

The system will be tested with:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing interactions between components
3. **AI Agent Tests**: Using Claude, GPT-4o, and Windsurf for real-world usage scenarios
4. **Performance Tests**: Validating performance under various memory loads
