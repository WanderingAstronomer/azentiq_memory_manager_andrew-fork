# Azentiq Memory Manager

A vendor-agnostic, tiered memory architecture for AI assistants.

## Overview

Memory Manager provides a flexible framework for managing memory in AI agents and assistants. It implements a tiered memory approach inspired by human memory systems:

- **Session Memory**: Short-term storage for the current interaction (Redis)
- **Working Memory**: Active information needed for reasoning (future implementation)
- **Long-term Memory**: Persistent knowledge storage with retrieval capabilities (future implementation)

## Features

### Tiered Memory Architecture

Inspired by human memory systems, the memory architecture is divided into tiers, each with specific purposes:

- **Short-term memory**: Recent conversation turns and ephemeral context
- **Working memory**: Important facts, preferences, and session state
- **Long-term memory**: Persistent knowledge and information

```python
# Example of using different memory tiers
from core.memory_manager import MemoryManager, MemoryTier

memory_manager = MemoryManager()

# Add to short-term memory (conversation turn)
memory_manager.add_memory(
    content="What's the weather like today?",
    metadata={"type": "conversation_turn", "role": "user"},
    tier=MemoryTier.SHORT_TERM
)

# Add to working memory (user preference)
memory_manager.add_memory(
    content="User prefers detailed explanations",
    metadata={"type": "preference"},
    tier=MemoryTier.WORKING,
    importance=0.8
)
```

### Redis Backend with Logical Separation

Memories are stored in Redis with logical separation using namespaces to organize and retrieve memories efficiently.

```python
# Redis key pattern used internally
redis_key = f"memory:{tier}:{session_id}:{component_id}:{memory_id}"

# Example: memory:working:default:main:04c169ca-2a45-44b3-9338-63fada870dad
```

### Automatic TTL Management

Short-term memories automatically expire after a configurable time period (default: 30 minutes).

```python
# Adding a memory with custom TTL (in seconds)
memory_manager.add_memory(
    content="Remember this for 5 minutes only",
    tier=MemoryTier.SHORT_TERM,
    ttl=300  # 5 minutes in seconds
)

# Default TTL for short-term is applied automatically if not specified
memory_manager.add_memory(
    content="This uses default TTL (30 minutes)",
    tier=MemoryTier.SHORT_TERM
)
```

### Token-Aware Memory Retrieval

Memories can be retrieved with awareness of token limits to optimize LLM prompt construction.

```python
# Generate a prompt with token budget constraint
prompt, token_usage = memory_manager.generate_prompt(
    session_id="user123",
    system_message="You are a helpful assistant.",
    user_query="What were my preferences again?",
    max_tokens=1000  # Token budget for memories
)

print(f"Prompt generated with {token_usage} tokens")
```

### Metadata Filtering and Advanced Search

Memories can be searched and filtered based on metadata attributes.

```python
# Search memories by metadata
user_preferences = memory_manager.search_memories(
    metadata_filter={"type": "preference", "session_id": "user123"}
)

# Advanced search combining filters
important_facts = memory_manager.search_memories(
    metadata_filter={"type": "fact"},
    min_importance=0.7,
    session_id="user123"
)
```

### Rich CLI for Memory Management

A command-line interface for interacting with the memory system.

```bash
# Add a memory via CLI
python -m cli.main add "User prefers dark mode" --tier working --importance 0.8 \
  --metadata '{"type":"preference", "session_id":"user123"}'

# Search memories by metadata
python -m cli.main search '{"type":"preference"}'

# List all memories in working tier
python -m cli.main list --tier working
```

### RESTful API Service with FastAPI

A full-featured API service for managing memories programmatically.

```python
import requests

api_url = "http://localhost:8000"

# Create a memory via API
response = requests.post(
    f"{api_url}/memories",
    json={
        "content": "User's favorite color is blue",
        "metadata": {"type": "preference"},
        "tier": "working",
        "importance": 0.7
    }
)

memory = response.json()
print(f"Created memory with ID: {memory['memory_id']}")
```

### Comprehensive API Documentation

Interactive Swagger UI documentation available at http://localhost:8000/docs for exploring and testing API endpoints.

### Full CRUD Operations for Memories

Complete Create, Read, Update, Delete operations for memories via API endpoints.

```python
import requests

api_url = "http://localhost:8000"
memory_id = "your-memory-id"

# Create a memory
response = requests.post(
    f"{api_url}/memories",
    json={"content": "New memory content", "tier": "working"}
)

# Read a memory
response = requests.get(f"{api_url}/memories/{memory_id}")

# Update a memory
response = requests.put(
    f"{api_url}/memories/{memory_id}",
    json={"content": "Updated content", "importance": 0.9}
)

# Delete a memory
response = requests.delete(f"{api_url}/memories/{memory_id}")
```

### Session and Conversation Management

Manage conversation turns and session context through dedicated API endpoints.

```python
import requests

api_url = "http://localhost:8000"
session_id = "user123"

# Add a conversation turn
response = requests.post(
    f"{api_url}/sessions/{session_id}/turns",
    json={
        "content": "What's the weather forecast?",
        "role": "user",
        "importance": 0.7
    }
)

# Get recent conversation history
response = requests.get(f"{api_url}/sessions/{session_id}/turns")
history = response.json()
print(f"Retrieved {len(history['turns'])} conversation turns")
```

### Prompt Generation with Memory Integration

Generate prompts that automatically integrate relevant memories from different tiers.

```python
import requests

api_url = "http://localhost:8000"
session_id = "user123"

# Generate a prompt with integrated memories
response = requests.post(
    f"{api_url}/sessions/{session_id}/prompt",
    json={
        "system_message": "You are a helpful assistant.",
        "user_query": "What were my preferences again?",
        "include_working_memory": True,
        "max_short_term_turns": 5
    }
)

result = response.json()
print(f"Prompt with {result['token_usage']} tokens: {result['prompt'][:100]}...")
```

### Framework Adapters (LangChain, LangGraph, Google ADK)

Templates and adapters for integrating with popular frameworks like LangChain, LangGraph, and Google ADK.

#### LangChain Integration

```python
# Example LangChain integration template
from langchain.memory import BaseMemory
from core.memory_manager import MemoryManager

class AzentiqMemory(BaseMemory):
    memory_manager: MemoryManager
    session_id: str
    
    def __init__(self, redis_url="redis://localhost:6379/0", session_id="default"):
        self.memory_manager = MemoryManager(redis_url=redis_url)
        self.session_id = session_id
    
    def load_memory_variables(self, inputs):
        # Get relevant memories for the current context
        memories = self.memory_manager.get_recent_turns(self.session_id, n_turns=5)
        return {"memory": self._format_memories(memories)}
    
    def save_context(self, inputs, outputs):
        # Save the current turn
        user_input = inputs.get("input", "")
        ai_output = outputs.get("output", "")
        
        self.memory_manager.add_conversation_turn(
            session_id=self.session_id,
            content=user_input,
            role="user"
        )
        
        self.memory_manager.add_conversation_turn(
            session_id=self.session_id,
            content=ai_output,
            role="assistant"
        )
```

#### Google ADK Integration

Azentiq Memory Manager provides a dedicated adapter for Google's Agent Development Kit (ADK):

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

# Add a session to memory
from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.genai import types

# Create a session
session = Session(
    id="user123_session",
    app_name="my_agent",
    user_id="user123"
)

# Add events to session
user_content = types.Content(
    role="user",
    parts=[types.Part(text="What's the weather today?")]
)
session.events.append(Event(author="user", content=user_content))

# Store session in memory
await adk_memory_service.add_session_to_memory(session)

# Search memory
results = await adk_memory_service.search_memory(
    query="weather",
    session_id="user123_session",
    limit=5
)
```

See `adapters/ADKAdapter_readme.md` for detailed documentation on the Google ADK adapter.

### Extensible Architecture

Designed for adding new storage backends, memory tiers, and integrations.

```python
# Example of implementing a custom memory store
from core.interfaces import IMemoryStore, Memory

class CustomMemoryStore(IMemoryStore):
    def __init__(self, connection_string):
        # Initialize your custom storage backend
        self.db = YourCustomDatabase(connection_string)
    
    def add_memory(self, memory: Memory, namespace: str) -> str:
        # Custom implementation for storing a memory
        return self.db.insert(namespace, memory.to_dict())
    
    def get_memory(self, memory_id: str, namespace: str) -> Memory:
        # Custom implementation for retrieving a memory
        data = self.db.get(namespace, memory_id)
        return Memory.from_dict(data)
    
    # Implement other required methods
```

## Installation

### Prerequisites

- Python 3.11+
- Redis server (for the MVP)

### Using Poetry (recommended)

```bash
# Clone the repository
git clone https://github.com/azentiq/memory-manager.git
cd memory-manager

# Install with Poetry
poetry install
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/azentiq/memory-manager.git
cd memory-manager

# Install with pip
pip install -e .
```

## Redis Setup Options

Azentiq Memory Manager requires Redis for the session memory store. Here are several free options to get started:

### Option 1: Local Redis Installation

**Windows:**
```bash
# Using Windows Subsystem for Linux (WSL2) - Recommended
wsl --install  # If WSL not already installed
wsl sudo apt update && sudo apt install redis-server
wsl sudo service redis-server start

# Or use the Windows port (less recommended)
# Download from https://github.com/microsoftarchive/redis/releases
```

**macOS:**
```bash
# Using Homebrew
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### Option 2: Docker Container (Cross-platform)

```bash
# Pull and run Redis in a Docker container
docker run --name azentiq-redis -p 6379:6379 -d redis

# Verify it's running
docker ps | grep azentiq-redis
```

### Option 3: Free Cloud Redis

- [Redis Cloud](https://redis.com/try-free/) - Free tier with 30MB database
- [Upstash](https://upstash.com/) - Free tier with Redis database
- [Render](https://render.com/) - Free Redis instance with limitations

When using a cloud Redis instance, update your connection URL in the code or CLI commands.

## Quick Start

### CLI Usage

Use the CLI to interact with the memory system:

```bash
# Add a memory to short-term memory (with 30-minute TTL)
python -m cli.main add "What's the weather like today?" --tier short_term --importance 0.5 --metadata '{"type":"conversation_turn", "role":"user", "session_id":"abc123"}'

# Add a memory to working memory (no expiration)
python -m cli.main add "User prefers detailed explanations" --tier working --importance 0.8 --metadata '{"type":"session_context", "context_key":"preference", "session_id":"abc123"}'

# List all memories
python -m cli.main list

# List memories from a specific tier
python -m cli.main list --tier short_term

# Get a specific memory
python -m cli.main get <memory_id>

# Search memories by metadata
python -m cli.main search '{"session_id":"abc123"}'

# Search in a specific tier
python -m cli.main search '{"session_id":"abc123"}' --tier working

# Update a memory
python -m cli.main update <memory_id> --content "Updated content" --importance 0.9

# Delete a memory
python -m cli.main delete <memory_id>
```

### API Service

The Memory Manager can also be accessed through a RESTful API service built with FastAPI:

```bash
# Start the API service (Windows)
run_api_service.bat

# Start the API service (manually)
python -m services.run_api --reload
```

The API will be accessible at http://localhost:8000 with interactive documentation available at http://localhost:8000/docs.

#### Basic API Usage Example

```python
import requests

api_url = "http://localhost:8000"

# Create a memory
memory_data = {
    "content": "User prefers dark mode in all applications",
    "metadata": {
        "type": "preference",
        "source": "user_settings"
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

# For detailed API documentation, see the docs/api directory
```

### Python API Usage

Import and use the memory manager in your Python code:

```python
from core.memory_manager import MemoryManager, MemoryTier

# Initialize the memory manager with Redis connection
memory_manager = MemoryManager(redis_url="redis://localhost:6379/0", model_token_limit=8192)

# Example conversation flow
session_id = "session_123"  # Unique identifier for the conversation

# 1. Store user preferences in working memory (persists for the session)
memory_manager.store_session_context(
    session_id=session_id,
    key="name",
    value="John Doe",
    importance=0.9
)

memory_manager.store_session_context(
    session_id=session_id,
    key="preference",
    value="prefers technical explanations",
    importance=0.7
)

# 2. Add conversation turns to short-term memory (expires after TTL)
memory_manager.add_conversation_turn(
    session_id=session_id,
    content="Tell me about memory systems in AI",
    role="user"
)

memory_manager.add_conversation_turn(
    session_id=session_id,
    content="Memory systems in AI enable context retention across interactions...",
    role="assistant"
)

# 3. Generate prompt for next LLM call with optimized memory inclusion
prompt, token_stats = memory_manager.generate_prompt(
    session_id=session_id,
    system_message="You are a helpful AI assistant.",
    user_query="Continue our discussion about memory systems.",
    max_short_term_turns=5
)

# Log token usage
print(f"Total tokens: {token_stats['total']}")
print(f"Memory tokens: {token_stats['short_term'] + token_stats['working']}")
```

## Architecture

The Azentiq Memory Manager follows a modular, extensible architecture designed for flexibility and compatibility with various AI frameworks. Here's a detailed breakdown of each component:

### Core Module

The Core module defines the fundamental interfaces, data models, and the central `MemoryManager` class that orchestrates all memory operations.

```python
# Core components and their responsibilities
from core.interfaces import Memory, MemoryTier, IMemoryStore, IVectorStore
from core.memory_manager import MemoryManager

# Example: Creating a memory manager with custom configuration
manager = MemoryManager(
    redis_url="redis://localhost:6379/0",  # Storage connection
    model_token_limit=8192,                # LLM context window size
    default_ttl=1800,                      # Default TTL for short-term memory
    component_id="main"                     # Default component ID
)
```

Key classes in Core:
- `Memory`: Data model representing a memory item with content, metadata, and attributes
- `MemoryTier`: Enumeration of memory tiers (SHORT_TERM, WORKING, LONG_TERM)
- `IMemoryStore`: Interface for memory storage implementations
- `MemoryManager`: Main class providing the high-level API for memory operations

### Storage Module

The Storage module contains implementations for different storage backends, allowing memory persistence across various databases and storage systems.

```python
# Available storage implementations
from storage.redis_store import RedisStore       # Default Redis implementation
from storage.in_memory_store import MemoryStore  # In-memory testing store
# Future: SQLite, Vector stores, etc.

# Example: Initializing a Redis store directly
redis_store = RedisStore(redis_url="redis://localhost:6379/0")

# Store a memory directly (normally handled by MemoryManager)
memory_id = redis_store.add_memory(
    memory=memory_obj,
    namespace="memory:working:default:main"
)
```

Features:
- **Redis Store**: Primary implementation using Redis for high-performance, in-memory storage
- **Namespace Management**: Logical separation of memories using structured key patterns
- **TTL Support**: Automatic expiration of short-term memories
- **Transaction Support**: Atomic operations for data consistency

### Services Module

The Services module provides a RESTful API built with FastAPI for interacting with the memory system over HTTP.

```python
# Starting the API service
python -m services.run_api

# Available API endpoints
# GET /memories - List memories
# POST /memories - Create a memory
# GET /memories/{memory_id} - Get a specific memory
# PUT /memories/{memory_id} - Update a memory
# DELETE /memories/{memory_id} - Delete a memory
# POST /sessions/{session_id}/turns - Add conversation turn
# GET /sessions/{session_id}/turns - Get recent conversation turns
# POST /sessions/{session_id}/prompt - Generate a prompt with memory integration
```

Components:
- **API Routers**: Organized endpoint handlers for memories, sessions, and system operations
- **Request/Response Models**: Pydantic schemas for input validation and response formatting
- **Dependency Injection**: Clean separation of concerns for service components
- **Middleware**: Error handling, logging, and request processing

### CLI Module

The CLI module offers a command-line interface for direct interaction with the memory system, ideal for testing and administrative tasks.

```bash
# CLI command structure
python -m cli.main [command] [arguments] [options]

# Available commands
python -m cli.main add "Memory content" --tier working --importance 0.8
python -m cli.main get [memory_id]
python -m cli.main list --tier short_term
python -m cli.main search '{"type":"preference"}'
python -m cli.main update [memory_id] --content "New content"
python -m cli.main delete [memory_id]
```

Features:
- **CRUD Operations**: Full memory management capabilities
- **Search & Filtering**: Query memories by metadata and attributes
- **Formatting Options**: Configurable output formats
- **Batch Processing**: Operate on multiple memories with a single command

### Adapters Module

The Adapters module provides integration templates for popular AI frameworks like LangChain and LangGraph, enabling seamless memory integration with existing systems.

```python
# Example LangChain integration
from adapters.langchain import AzentiqMemoryAdapter

# Create a memory adapter for LangChain
memory_adapter = AzentiqMemoryAdapter(
    session_id="user123",
    redis_url="redis://localhost:6379/0"
)

# Use with LangChain
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

conversation = ConversationChain(
    llm=OpenAI(),
    memory=memory_adapter,
    verbose=True
)
```

Planned integrations:
- **LangChain**: Memory classes compatible with LangChain's memory interfaces
- **LangGraph**: State management within LangGraph workflows
- **Custom Agents**: Simplified memory integration for custom agent frameworks

### Utils Module

The Utils module contains helper utilities for token budgeting, prompt construction, memory prioritization, and other auxiliary functions.

```python
# Token budgeting components
from utils.token_budget import TokenEstimator, BudgetManager
from utils.prompt import PromptConstructor, MemoryFormatter
from utils.selection import PrioritySelector, RelevanceSelector

# Example: Using the token budget system
token_estimator = TokenEstimator()
tokens = token_estimator.estimate_tokens("This is some text to estimate")

# Example: Memory selection by relevance
selector = RelevanceSelector(token_estimator=token_estimator)
relevant_memories = selector.select_memories(
    memories=memories_list,
    query="What is the weather like?",
    max_tokens=1000
)
```

Key utilities:
- **Token Estimation**: Calculate token usage for memory content and prompts
- **Budget Management**: Distribute token budget across memory tiers
- **Memory Selection**: Prioritize memories by importance, recency, or relevance
- **Prompt Construction**: Format memories and build optimized prompts for LLMs

### Integration Architecture

The components interact in a layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                     Client Applications                  │
└───────────────┬─────────────────┬───────────────────────┘
                │                 │                        
┌───────────────▼─────┐ ┌────────▼────────┐ ┌────────────▼────────────┐
│      CLI Module      │ │  Services API   │ │     Adapters Module     │
└───────────┬─────────┘ └────────┬────────┘ └────────────┬────────────┘
            │                    │                        │             
            │          ┌─────────▼──────────┐            │             
            └──────────►   MemoryManager    ◄────────────┘             
                       └─────────┬──────────┘                          
                                 │                                     
                     ┌───────────▼────────────┐                        
                     │     Storage Module     │                        
                     └────────────────────────┘                        
```

This modular architecture allows for:
- **Flexible Deployment**: Use only the components you need
- **Multiple Interfaces**: CLI, API, or direct code integration
- **Customizable Storage**: Swap storage implementations without changing application logic
- **Framework Agnostic**: Integrate with any AI framework using adapters

## Testing

### Unit Testing

Azentiq Memory Manager includes a comprehensive suite of unit tests to ensure functionality and stability. These tests mock external dependencies like Redis to run independently.

#### Prerequisites

Install the test dependencies:

```bash
pip install pytest pytest-cov mock
```

#### Running Unit Tests

To run all unit tests:

```bash
# Run all tests with the unittest framework
python -m unittest discover

# Alternatively, use pytest with more detailed output
python -m pytest
```

To run tests for a specific component:

```bash
# Test just the Memory Manager
python -m unittest tests.test_memory_manager

# Test just the Redis Store
python -m unittest tests.storage.test_redis_store
```

#### Test Coverage

To generate a test coverage report:

```bash
# Run coverage and generate report
coverage run -m unittest discover
coverage report -m

# For HTML output (creates htmlcov/ directory)
coverage html
```

The current test coverage is approximately 76%.

### Integration Testing

Integration tests that validate functionality with a real Redis instance are available in the `tests/integration` directory. See the integration testing documentation for details on setting up and running these tests.

## Token Budgeting System

Azentiq Memory Manager includes a sophisticated token budgeting system that manages memory selection and adaptation based on token constraints. This system has been refactored into a modular, extensible architecture:

### Token Estimation

The `TokenEstimator` class provides accurate token count estimates for memories and text:

```python
from utils.token_budget import TokenEstimator

# Create estimator with custom parameters
estimator = TokenEstimator(config={"chars_per_token": 4})

# Estimate tokens for text
token_count = estimator.estimate_text("Some text to analyze")

# Estimate tokens for a memory object
memory_tokens = estimator.estimate_memory(memory_object)
```

### Memory Selection Strategies

The system includes pluggable memory selection strategies that can be extended with custom implementations:

```python
from utils.token_budget.selection import PriorityMemorySelector, RelevanceMemorySelector

# Create selectors
priority_selector = PriorityMemorySelector(token_estimator)
relevance_selector = RelevanceMemorySelector(token_estimator)

# Select memories by priority (recency + importance)
selected_memories = priority_selector.select_memories(
    memories_list, 
    max_tokens=1000,
    recency_weight=0.6,
    importance_weight=0.4
)

# Select memories by relevance to a query
relevant_memories = relevance_selector.select_memories(
    memories_list,
    query="What is the weather like?",
    max_tokens=1000,
    relevance_threshold=0.2
)
```

### Memory Adaptation Strategies

When token budgets are exceeded, the system applies adaptation strategies to reduce memory usage:

```python
from utils.token_budget.adaptation import (
    ReduceAdaptationStrategy, 
    SummarizeAdaptationStrategy,
    PrioritizeTierStrategy
)

# Create adaptation strategies
reduce_strategy = ReduceAdaptationStrategy(token_estimator)
summarize_strategy = SummarizeAdaptationStrategy(token_estimator, summarizer_fn)
prioritize_strategy = PrioritizeTierStrategy(token_estimator)

# Apply a strategy to reduce token usage
updated_memories, new_token_count, removed_ids = reduce_strategy.adapt_memories(
    memories_dict,
    used_tokens=5000,
    target_tokens=4000,
    reduction_target=0.2
)
```

### Prompt Construction

The system provides flexible prompt construction with memory formatting:

```python
from utils.token_budget.prompt import MemoryFormatter, PromptConstructor
from utils.token_budget import TokenEstimator

# Create formatter with custom template
formatter = MemoryFormatter(
    default_format_template="[Memory {index}] {content} (Importance: {importance})\n"
)

# Format individual memories or sections
formatted_memory = formatter.format_memory(memory_object, index=1)
formatted_section = formatter.format_memories(
    memory_list,
    section_title="Recent Conversations"
)

# Create prompt constructor
constructor = PromptConstructor(token_estimator=TokenEstimator())

# Construct a prompt with memories
prompt, token_stats = constructor.construct_prompt(
    user_input="What's the weather like?",
    memory_sections={
        "short_term": short_term_memories,
        "working": working_memories
    },
    max_tokens=4000,
    system_message="You are a helpful assistant.",
    format_templates={
        "short_term": "User: {content}\n",
        "working": "Context: {content} (Importance: {importance})\n"
    }
)
```

### Integrated Management

The `TokenBudgetManager` class integrates all these components:

```python
from utils.token_budget import TokenBudgetManager

# Create manager with total token budget and config
manager = TokenBudgetManager(
    total_budget=8192,
    config=config_dict,
    budget_rules_manager=rules_manager
)

# Set component context
manager.set_context(component_id="agent_planner", session_id="session123")

# Generate prompt with selected memories
prompt, token_stats = manager.construct_prompt_with_memories(
    user_input="What was my last question?",
    memories={
        "short_term": short_term_memories,
        "working": working_memories,
        "relevance": relevant_memories
    },
    max_tokens=7000,
    system_message="You are a helpful assistant with access to memories."
)
```

This modular design allows for easy extension, maintenance, and testing of the token budgeting components.

## Memory Namespacing

The system implements a comprehensive namespacing strategy to logically separate memories across tiers, frameworks, and components. The namespace pattern is:

```
{tier}:{session_id}:{framework}:{component_id}:{memory_id}
```

For example: `short_term:session123:langchain:planner:550e8400-e29b-41d4-a716-446655440000`

### Setting Component Context

The `MemoryManager` and underlying storage systems support component context propagation:

```python
# Set the current component context
manager = MemoryManager(framework="langchain")
manager.set_context(component_id="planner")

# All subsequent memory operations use this context
memory_id = manager.add_memory(
    content="Important planning information",
    metadata={"task_id": "T123"},
    session_id="session456"
)

# Memories can be filtered by tier, session, or framework
memories = manager.list_memories(tier=MemoryTier.WORKING, session_id="session456")
```

### Namespacing Benefits

- **Framework Integration**: Clear separation between different frameworks (app, LangChain, LangGraph)
- **Component Isolation**: Each component's memories are isolated yet accessible
- **Session Management**: Session context is preserved across components
- **Efficient Filtering**: Optimized retrieval and search operations by namespace

## Memory Tiers

Azentiq Memory Manager implements a tiered memory system that mimics cognitive memory processes:

### Short-Term Memory (STM)
- Stores conversation turns and contextual information
- Auto-expires after a configurable period (default: 30 minutes)
- Tagged with `type: "conversation_turn"` metadata
- Optimized for recency-based retrieval
- Uses Redis key prefix `stm:{session_id}:`

### Working Memory (WM)
- Stores important session context that persists throughout the interaction
- No expiration (lasts for the entire session)
- Tagged with `type: "session_context"` metadata
- Optimized for importance-based retrieval
- Uses Redis key prefix `wm:{session_id}:`

### Long-Term Memory (future)
- Will store persistent knowledge with vector-based retrieval
- Not included in the current MVP

## Token Budget Management

The `TokenBudgetManager` utility helps optimize memory retrieval for LLM prompt construction:

```python
# Example usage
from core.memory_manager import MemoryManager

# Initialize with model token limit
memory_manager = MemoryManager(model_token_limit=8192)

# Add conversation turns
memory_manager.add_conversation_turn(
    session_id="user123",
    content="What's the weather like?",
    role="user"
)

# Store important context in working memory
memory_manager.store_session_context(
    session_id="user123", 
    key="user_preference", 
    value="prefers detailed explanations",
    importance=0.8
)

# Generate a prompt with optimized memory inclusion
prompt, token_stats = memory_manager.generate_prompt(
    session_id="user123",
    system_message="You are a helpful assistant.",
    user_query="Tell me about the weather.",
    max_short_term_turns=10,
    include_working_memory=True
)

# Check token usage statistics
print(f"Total tokens used: {token_stats['total']}")
print(f"Short-term memory tokens: {token_stats['short_term']}")
print(f"Working memory tokens: {token_stats['working']}")
```

The system automatically:
- Estimates token usage for each memory item
- Allocates token budget between different memory tiers
- Selects memories based on tier-specific strategies (recency vs importance)
- Formats memories for prompt inclusion
- Tracks token usage statistics

## Schema Specification (v1.0)

Azentiq Memory Manager follows a well-defined schema for managing memories in agentic applications. This specification defines the structure and behavior of the memory system for version 1.0.

### Memory Schema

```yaml
version: "1.0"

memory_item:
  id: string                      # Unique identifier (UUID)
  content: string                 # The actual memory content
  metadata:
    type: string                  # Memory type (conversation_turn, session_context, etc.)
    session_id: string            # Session identifier for scoping
    created_at: datetime          # Creation timestamp
    updated_at: datetime          # Last update timestamp
    importance: float             # Importance score (0.0-1.0)
    component_id: string          # Identifier of the component that created the memory (optional)
    framework: string             # Originating framework (app, langchain, langgraph, etc.) (optional)
    # Additional metadata fields based on type
  tier: enum                      # Memory tier (SHORT_TERM, WORKING, LONG_TERM)
  ttl: int                        # Time-to-live in seconds (null = no expiration)
```

### Agentic Configuration Schema

For multi-component agentic workflows, the system can be configured using the following YAML schema:

```yaml
version: "1.0"
application:
  name: string                    # Application name
  default_model: string           # Default LLM model
  global_token_limit: int         # Global token limit for the application
  
memory_tiers:
  short_term:
    ttl_seconds: int              # Time-to-live in seconds (default: 1800)
    default_importance: float     # Default importance (0.0-1.0)
  working:
    ttl_seconds: null             # No expiration by default
    default_importance: float     # Default importance (0.0-1.0)
  long_term:
    storage: string               # Storage type (e.g., "vector")
    embedding_model: string       # Embedding model for vector storage
    
components:
  - id: string                    # Component identifier
    type: string                  # Component type (agent, tool, workflow)
    model: string                 # LLM model for this component (optional)
    token_limit: int              # Token limit for this component
    memory_allocation:
      short_term: float           # Portion of token budget for short-term (0.0-1.0)
      working: float              # Portion of token budget for working memory (0.0-1.0)
      long_term: float            # Portion of token budget for long-term (0.0-1.0)
    memory_priority: string       # Priority level (low, medium, high)
    framework: string             # Framework (app, langchain, langgraph)
    
workflows:
  - id: string                    # Workflow identifier
    components: [string]          # List of component IDs in this workflow
    memory_inheritance:
      - from: string              # Source component ID
        to: string                # Target component ID
        metadata_filter:          # Filter for which memories to inherit
          type: string            # Type of memories to inherit
    
memory_policies:
  - name: string                  # Policy name
    action: string                # Action to take (e.g., "prioritize_by_importance")
```

### Memory Namespacing

Memories are namespaced using the following pattern:

```
{tier}:{session_id}:{framework}:{component_id}:{memory_id}
```

Example:
```
stm:session123:langchain:planner:550e8400-e29b-41d4-a716-446655440000
```

This allows for efficient retrieval and isolation of memories across components, frameworks, and tiers.

### Token Budget Distribution

Token budgets are distributed according to the following formulas:

1. **Component Budget**: `component_token_limit` or `global_token_limit` if not specified
2. **Tier Budget**: `component_budget * memory_allocation[tier]`
3. **Priority Adjustment**: When token constraints require pruning, memories are prioritized by:
   - Memory priority of the component
   - Importance score of individual memories
   - Recency (for short-term memories)
   - Relevance (for long-term memories)

## Contributing

Contributions are welcome! Areas of focus:

1. Implementing LangChain and LangGraph adapters
2. Adding working memory and long-term memory implementations
3. Improving test coverage
4. Documentation and examples

## License

Apache 2.0