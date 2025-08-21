# Google ADK Adapter for Azentiq Memory Manager

This adapter enables Azentiq Memory Manager to serve as a drop-in replacement for Google Agent Development Kit (ADK) memory services. It implements the Google ADK memory service functionality using Azentiq Memory Manager's rich memory management capabilities.

## Overview

The adapter bridges the gap between Google ADK's simpler memory model and Azentiq Memory Manager's sophisticated tiered memory architecture. It allows applications built with Google ADK to leverage Azentiq's enhanced memory features:

- Tiered memory system (SHORT_TERM, WORKING, LONG_TERM)
- Importance-based memory retention
- Rich metadata filtering
- Token-aware memory management
- Configurable TTL (Time-To-Live) settings

## Installation

1. Ensure that you have installed Azentiq Memory Manager
2. Install Google ADK (optional - the adapter provides mock implementations if ADK is unavailable)
   ```bash
   pip install google-adk
   ```

## Usage

### Basic Usage

```python
from adapters.adk_adapter import AzentiqAdkMemoryAdapter
from core.interfaces import MemoryTier

# Initialize the adapter
adk_memory_service = AzentiqAdkMemoryAdapter(
    redis_url="redis://localhost:6379/0",
    default_tier=MemoryTier.SHORT_TERM,
    default_importance=0.5,
    default_ttl=3600  # 1 hour in seconds
)

# Use it in your ADK agent
agent = YourAdkAgent(memory_service=adk_memory_service)
```

### Using with Existing Memory Manager

```python
from core.memory_manager import MemoryManager
from adapters.adk_adapter import AzentiqAdkMemoryAdapter

# Use an existing memory manager
memory_manager = MemoryManager(redis_url="redis://localhost:6379/0")
adk_adapter = AzentiqAdkMemoryAdapter(memory_manager=memory_manager)
```

### Adding Session to Memory

```python
# ADK session and event objects (from ADK framework)
from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.genai import types

# Create a session
session = Session(
    id="user123_session",
    app_name="my_agent",
    user_id="user123"
)

# Add user event to the session
user_content = types.Content(
    role="user",
    parts=[types.Part(text="What's the weather today?")]
)
user_event = Event(
    author="user",
    content=user_content
)
session.events.append(user_event)

# Add assistant event to the session
assistant_content = types.Content(
    role="assistant",
    parts=[types.Part(text="The weather is sunny with a high of 75°F.")]
)
assistant_event = Event(
    author="assistant",
    content=assistant_content
)
session.events.append(assistant_event)

# Store session in memory
await adk_adapter.add_session_to_memory(session)
```

### Searching Memory

```python
# Search memory
results = await adk_adapter.search_memory(
    query="weather",
    session_id="user123_session",
    limit=5
)

# Process results
for memory in results:
    print(f"Content: {memory['content']}")
    print(f"Role: {memory['metadata']['role']}")
```

## Key Concepts

### Session and Event Mapping

Google ADK's sessions and events are mapped to Azentiq Memory Manager as follows:

- **Session ID** (`session.id`) is stored in memory metadata as `session_id`
- **App Name** is stored in memory metadata as `app_name`
- **User ID** is stored in memory metadata as `user_id` if available
- **Events** from the session's `events` list are stored as individual memories with metadata including:
  - `role` (from event content's role or author field)
  - `author` (from event's author field)
  - `message_index` (sequence in conversation)
  - `adk_source` (flag to identify ADK-sourced memories)
  - `adk_timestamp` (timestamp from the event if available)

### Memory Tier Mapping

By default, ADK memories are stored in the SHORT_TERM tier, but this is configurable:

```python
# Store ADK memories in WORKING tier
adapter = AzentiqAdkMemoryAdapter(default_tier=MemoryTier.WORKING)
```

### Importance Scoring

The adapter automatically assigns importance scores to memories based on:

1. Default importance value (configurable)
2. Content length (longer content gets slightly higher importance)
3. Role (user messages get slightly higher importance)

Custom importance calculation can be implemented by extending the `AzentiqAdkMemoryAdapter` class.

## Advanced Configuration

### Custom Memory Transformation

You can extend the adapter to customize how ADK memories are transformed:

```python
class CustomAdkAdapter(AzentiqAdkMemoryAdapter):
    def _calculate_importance(self, content, role):
        # Custom importance calculation logic
        if "critical" in content.lower():
            return 0.9
        return super()._calculate_importance(content, role)
    
    def _convert_to_adk_memory(self, azentiq_memory):
        # Custom conversion logic
        adk_memory = super()._convert_to_adk_memory(azentiq_memory)
        # Add additional fields or modify conversion
        return adk_memory
```

### Utility Functions

The adapter provides utility functions to help with common tasks:

```python
from adapters.adk_adapter import session_from_azentiq_memories

# Get memories from Azentiq
memories = memory_manager.get_memories_by_metadata(
    {"session_id": "user123_session"}, 
    tier=MemoryTier.SHORT_TERM
)

# Convert to an ADK session
session = session_from_azentiq_memories(memories)
```

## Error Handling

The adapter includes error handling and logging for robust operation:

- Graceful fallback if ADK is not installed
- Logging for debugging and monitoring
- Exception handling for memory operations

## Limitations and Considerations

1. **ADK Version Compatibility**: The adapter is designed for ADK's memory service interface. If Google updates this interface, the adapter may need updating.

2. **Memory Transformation**: Some information might not map perfectly between systems due to differences in data models.

3. **Performance**: Searching across multiple tiers may impact performance for very large memory stores.

## Development and Testing

### Test Suite

To contribute to the adapter:

1. Ensure you have both Azentiq Memory Manager and Google ADK installed
2. Run test suite: `python -m unittest tests.adapters.test_adk_adapter`
3. Add new tests for any modified functionality

### Sample Tests and Integration

Several sample tests are provided to demonstrate and validate the integration:

1. **Simple Session Test** (`samples/adk_weather_agent/simple_session_test.py`)
   - Basic test for ADK Session and Event creation
   - Demonstrates correct usage of ADK objects and event handling

2. **Memory Adapter Test** (`samples/adk_weather_agent/adk_memory_adapter_test.py`)
   - Focused test for the adapter functionality
   - Tests adding session to memory and memory search capabilities
   - Can run with either real or mock ADK implementations

3. **Weather Agent Example** (`samples/adk_weather_agent/adk_weather_agent.py`)
   - Full integration example with a functional weather agent
   - Demonstrates tool creation, session management, and memory integration
   - Shows how to use the adapter in a real-world scenario

4. **GitHub ADK Test** (`samples/adk_weather_agent/github_adk_test.py`)
   - Test with the official GitHub version of Google ADK
   - Validates compatibility with the latest ADK version

Run these samples to verify your installation and understand integration patterns.
