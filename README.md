# Azentiq Memory Manager

A vendor-agnostic, tiered memory architecture for AI assistants.

## Overview

Memory Manager provides a flexible framework for managing memory in AI agents and assistants. It implements a tiered memory approach inspired by human memory systems:

- **Session Memory**: Short-term storage for the current interaction (Redis)
- **Working Memory**: Active information needed for reasoning (future implementation)
- **Long-term Memory**: Persistent knowledge storage with retrieval capabilities (future implementation)

## Features

- ✅ Tiered memory architecture (short-term and working memory)
- ✅ Redis backend with logical separation of memory tiers
- ✅ Automatic TTL management for short-term memory (defaults to 30 minutes)
- ✅ Token-aware memory retrieval for optimized LLM prompts
- ✅ Metadata filtering and advanced search
- ✅ Rich CLI for interacting with memory tiers
- ✅ Templates for LangChain and LangGraph adapters
- ✅ Designed for extensibility with additional backends

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

Memory Manager is designed with a modular architecture:

- **Core**: Defines the interfaces and the main `MemoryManager` class
- **Storage**: Implements different storage backends (Redis, SQLite, vector stores)
- **CLI**: Command-line interface for interacting with the system
- **Adapters**: Integration with popular frameworks like LangChain and LangGraph (future)
- **Utils**: Helper utilities including token budgeting, prompt construction, and memory prioritization

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