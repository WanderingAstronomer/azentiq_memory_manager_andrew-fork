# Google ADK Integration Architecture

## Overview

This document outlines the architectural considerations, design decisions, and recommended approaches for integrating Azentiq Memory Manager with Google's Agent Development Kit (ADK). It serves as a technical reference for developers implementing enterprise agent solutions that leverage both systems.

## System Integration Architecture

### Architecture Diagram

```
┌───────────────────┐     ┌────────────────────────────┐
│                   │     │                            │
│  Google ADK       │     │  Azentiq Memory Manager    │
│  Agent Framework  │     │                            │
│                   │     │  ┌─────────────────────┐   │
│  ┌─────────────┐  │     │  │                     │   │
│  │   ADK       │  │     │  │  SHORT_TERM Memory  │   │
│  │   Agent     ├──┼─────┼─▶│                     │   │
│  └─────┬───────┘  │     │  └─────────────────────┘   │
│        │          │     │                            │
│        │          │     │  ┌─────────────────────┐   │
│  ┌─────▼───────┐  │     │  │                     │   │
│  │  ADK        │  │     │  │  WORKING Memory     │   │
│  │  Memory     ├──┼─────┼─▶│                     │   │
│  │  Interface  │  │     │  └─────────────────────┘   │
│  │             │◀─┼─────┼──┐                         │
│  └─────────────┘  │     │  │ ┌─────────────────────┐ │
│                   │     │  │ │                     │ │
└───────────────────┘     │  └─▶ LONG_TERM Memory    │ │
                          │    │                     │ │
                          │    └─────────────────────┘ │
                          │                            │
┌───────────────────┐     └────────────────────────────┘
│                   │
│  AzentiqAdkMemory │
│  Adapter          │
│                   │
└───────────────────┘
```

### Key Components

1. **Google ADK Agent Framework**: The ADK-based agent implementation that provides the core agent capabilities.
2. **Azentiq Memory Manager**: The tiered memory system that provides sophisticated memory capabilities.
3. **AzentiqAdkMemoryAdapter**: A bridge component that implements Google ADK's `BaseMemoryService` interface while leveraging Azentiq's Memory Manager.

## Integration Design Decisions

### 1. Adapter Pattern vs. Direct Integration

**Chosen Approach**: Adapter Pattern

Rather than modifying the core Azentiq Memory Manager or forcing agents to use Azentiq's native interfaces, we've implemented an adapter layer (`AzentiqAdkMemoryAdapter`) that maps Google ADK memory concepts to Azentiq memory concepts. This ensures:

- **Loose coupling**: Azentiq Memory Manager and Google ADK can evolve independently
- **Minimal intrusion**: No changes to either system's core code
- **Flexibility**: Different mapping strategies can be implemented by modifying the adapter

### 2. Memory Tier Mapping

**Approach**: Configurable default mapping with customization options

Google ADK doesn't have an explicit concept of memory tiers, while Azentiq has SHORT_TERM, WORKING, and LONG_TERM tiers. Our adapter:

- Maps ADK memories to configurable default tiers based on memory characteristics
- Allows per-memory tier customization via metadata
- Preserves tier information in metadata when converting between systems

### 3. Session and Memory Metadata Handling

**Approach**: Rich metadata preservation and augmentation

The adapter:

- Preserves all ADK session metadata within Azentiq memories
- Adds adapter-specific metadata (e.g., `adk_source: true`) for identification
- Maps ADK session IDs to Azentiq session IDs in a consistent way
- Includes timestamp conversions for proper temporal ordering

### 4. Memory Search and Retrieval

**Approach**: Multi-tier semantic search with metadata filtering

The adapter implements ADK's `search_memory` by:

- Searching across multiple Azentiq memory tiers
- Prioritizing results from SHORT_TERM over WORKING over LONG_TERM
- Filtering by session ID when provided
- Converting Azentiq memory objects back to ADK memory format

## Implementation Guidelines

### Integration Patterns

#### 1. Standard Integration

Most suitable for new projects starting with Google ADK:

```python
from adapters.adk_adapter import AzentiqAdkMemoryAdapter
from core.memory_manager import MemoryManager

# Initialize Azentiq Memory Manager
memory_manager = MemoryManager()

# Create ADK adapter with Azentiq backend
adk_memory_service = AzentiqAdkMemoryAdapter(
    memory_manager=memory_manager,
    default_tier=MemoryTier.SHORT_TERM,  # For conversation history
    default_importance=0.5,
    default_ttl=3600  # 1 hour
)

# Initialize ADK agent with Azentiq memory
agent = Agent(
    memory_service=adk_memory_service,
    # ... other ADK agent configuration
)
```

#### 2. Dual-Interface Pattern

For projects that need to access both ADK and Azentiq interfaces:

```python
# Initialize shared memory system
memory_manager = MemoryManager()

# Create ADK adapter
adk_memory = AzentiqAdkMemoryAdapter(memory_manager)

# Both interfaces can be used in the application
# ADK interface:
await adk_memory.add_session_to_memory(session)

# Direct Azentiq interface (for advanced features):
memory_manager.add_memory(
    content="Important information",
    importance=0.9,
    tier=MemoryTier.LONG_TERM
)
```

#### 3. Mock-Compatible Testing Pattern

For development without dependencies:

```python
# Determine if we should use mock components
use_mock = True  # Or based on environment configuration

if use_mock:
    # Create mock components
    memory_manager = MockMemoryManager()
    adk_memory = AzentiqAdkMemoryAdapter(memory_manager)
else:
    # Create real components
    memory_manager = MemoryManager(redis_url="redis://localhost:6379")
    adk_memory = AzentiqAdkMemoryAdapter(memory_manager)
```

## Performance Considerations

1. **Memory Tier Management**:
   - SHORT_TERM should be used for recent conversation history
   - WORKING for extracted user preferences and active context
   - LONG_TERM for persistent information across sessions

2. **Memory Importance Scoring**:
   - Use higher importance scores (0.7-1.0) for critical user preferences
   - Use medium importance (0.3-0.7) for contextual information
   - Use lower importance (0-0.3) for routine conversation turns

3. **TTL Management**:
   - SHORT_TERM memories benefit from shorter TTLs (minutes to hours)
   - WORKING memories may need medium TTLs (hours to days)
   - LONG_TERM memories should have longer TTLs (weeks to months) or none

4. **Search Optimization**:
   - When possible, include session ID in search operations
   - Use tier-specific searches for faster retrieval when appropriate
   - Consider metadata-based searches for well-structured data

## Known Limitations

1. **Metadata Structure Differences**:
   - ADK memories have a simpler metadata structure than Azentiq
   - Some advanced Azentiq metadata may not be fully represented in ADK format

2. **Memory Importance**:
   - ADK doesn't have a direct equivalent to Azentiq's importance scoring
   - The adapter assigns default importance which may need tuning

3. **Async API Differences**:
   - ADK uses async patterns while some Azentiq methods are synchronous
   - The adapter handles this difference but may introduce minimal overhead

4. **Memory Format Conversions**:
   - Frequent conversions between ADK and Azentiq formats have performance costs
   - Consider batch operations where possible

## Future Enhancements

1. **Improved Memory Mapping Intelligence**:
   - Enhanced algorithms for determining optimal memory tiers
   - Content-based importance scoring

2. **Caching Layer**:
   - Optional caching to reduce database calls for frequent memory operations

3. **Advanced Search Capabilities**:
   - Better integration with vector search and semantic search capabilities

4. **Migration Tools**:
   - Utilities for migrating existing ADK memories to Azentiq format

## Conclusion

The adapter-based integration of Google ADK with Azentiq Memory Manager provides a robust, flexible foundation for enterprise agent development. By leveraging Azentiq's tiered memory architecture with ADK's agent framework, developers can create agents with sophisticated memory capabilities while maintaining compatibility with the Google ecosystem.
