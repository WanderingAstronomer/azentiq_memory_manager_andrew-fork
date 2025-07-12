"""Integration tests for Azentiq Memory Manager workflows.

These tests verify end-to-end functionality using a real Redis instance.
"""

import os
import time
import uuid
import pytest
from datetime import datetime
from typing import Dict, List, Generator, Any

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.interfaces import Memory, MemoryTier
from storage.redis_store import RedisStore
from memory_manager import MemoryManager


# Test configuration - can be overridden with environment variables
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379")
TEST_PREFIX = f"test_integration_{uuid.uuid4().hex[:8]}:"  # Unique prefix for this test run


@pytest.fixture(scope="module")
def redis_store() -> Generator[RedisStore, None, None]:
    """Create a Redis store for testing with a unique prefix."""
    store = RedisStore(
        redis_url=REDIS_URL,
        prefix=TEST_PREFIX,
        expire_seconds=60,  # Short expiry for tests
        framework="test_framework"
    )
    
    # Check Redis connection
    try:
        store.client.ping()
    except Exception as e:
        pytest.skip(f"Redis not available at {REDIS_URL}: {e}")
    
    yield store
    
    # Cleanup: delete all keys with our test prefix
    for key in store.client.keys(f"{TEST_PREFIX}*"):
        store.client.delete(key)


@pytest.fixture(scope="module")
def memory_manager(redis_store: RedisStore) -> MemoryManager:
    """Create a memory manager with our test Redis store."""
    return MemoryManager(redis_store=redis_store)


@pytest.fixture
def unique_session_id() -> str:
    """Generate a unique session ID for tests."""
    return f"test_session_{uuid.uuid4().hex[:8]}"


def test_add_retrieve_memory(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test the basic flow of adding and retrieving a memory."""
    # Add a new memory
    memory_id = memory_manager.add_memory(
        content="This is a test memory for integration testing",
        metadata={"source": "integration_test", "topic": "memory_retrieval"},
        importance=0.8,
        tier=MemoryTier.WORKING,
        session_id=unique_session_id
    )
    
    assert memory_id is not None, "Memory ID should be returned"
    
    # Retrieve the memory using the ID
    memory = memory_manager.get_memory(
        memory_id=memory_id,
        tier=MemoryTier.WORKING,
        session_id=unique_session_id
    )
    
    # Verify memory content and attributes
    assert memory is not None, "Memory should be found"
    assert memory.memory_id == memory_id
    assert memory.content == "This is a test memory for integration testing"
    assert memory.metadata["source"] == "integration_test"
    assert memory.metadata["topic"] == "memory_retrieval"
    assert memory.importance == 0.8
    assert memory.tier == MemoryTier.WORKING


def test_search_by_metadata(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test adding multiple memories and searching by metadata."""
    # Create test data
    test_memories = [
        {"content": "Memory about Python", "metadata": {"language": "python", "category": "programming"}},
        {"content": "Memory about JavaScript", "metadata": {"language": "javascript", "category": "programming"}},
        {"content": "Memory about Redis", "metadata": {"technology": "redis", "category": "database"}},
    ]
    
    # Add all memories
    memory_ids = []
    for mem in test_memories:
        memory_id = memory_manager.add_memory(
            content=mem["content"],
            metadata=mem["metadata"],
            importance=0.7,
            tier=MemoryTier.WORKING,
            session_id=unique_session_id
        )
        memory_ids.append(memory_id)
    
    # Search for programming languages
    programming_memories = memory_manager.search_by_metadata(
        query={"category": "programming"},
        tier=MemoryTier.WORKING,
        limit=10
    )
    
    # Verify results
    assert len(programming_memories) == 2, "Should find 2 programming memories"
    languages = [m.metadata.get("language") for m in programming_memories]
    assert "python" in languages
    assert "javascript" in languages
    
    # Search for Redis technology
    redis_memories = memory_manager.search_by_metadata(
        query={"technology": "redis"},
        tier=MemoryTier.WORKING,
        limit=10
    )
    
    assert len(redis_memories) == 1, "Should find 1 Redis memory"
    assert redis_memories[0].content == "Memory about Redis"


def test_update_memory(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test updating a memory and retrieving the updated version."""
    # Add a new memory
    memory_id = memory_manager.add_memory(
        content="Initial content",
        metadata={"status": "draft"},
        importance=0.5,
        tier=MemoryTier.WORKING,
        session_id=unique_session_id
    )
    
    # Get the memory
    memory = memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id)
    assert memory is not None
    
    # Update the memory
    memory.content = "Updated content"
    memory.metadata["status"] = "final"
    memory.importance = 0.9
    
    # Save the update
    memory_manager.update_memory(memory, session_id=unique_session_id)
    
    # Retrieve again to verify updates
    updated_memory = memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id)
    assert updated_memory is not None
    assert updated_memory.content == "Updated content"
    assert updated_memory.metadata["status"] == "final"
    assert updated_memory.importance == 0.9


def test_generate_prompt(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test the prompt generation with real memories."""
    # Add conversation memories (short-term)
    for turn_idx, turn in enumerate([
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a high-level programming language."},
        {"role": "user", "content": "Tell me about Redis."},
        {"role": "assistant", "content": "Redis is an in-memory data structure store."}
    ]):
        memory_manager.add_memory(
            content=turn["content"],
            metadata={
                "role": turn["role"],
                "turn": turn_idx
            },
            importance=1.0,
            tier=MemoryTier.SHORT_TERM,
            session_id=unique_session_id
        )
    
    # Add some working memories
    memory_manager.add_memory(
        content="Redis is used for caching, session management, and as a message broker.",
        metadata={"topic": "redis", "type": "fact"},
        importance=0.8,
        tier=MemoryTier.WORKING,
        session_id=unique_session_id
    )
    
    # Generate a prompt with these memories
    system_message = "You are a helpful AI assistant with access to conversation history and facts."
    user_query = "Can I use Redis with Python?"
    
    prompt, stats = memory_manager.generate_prompt(
        session_id=unique_session_id,
        system_message=system_message,
        user_query=user_query,
        max_short_term_turns=4,
        include_working_memory=True
    )
    
    # Basic verification
    assert system_message in prompt, "System message should be in prompt"
    assert user_query in prompt, "User query should be in prompt"
    assert "Python is a high-level programming language" in prompt, "Short-term memory should be included"
    assert "Redis is used for caching" in prompt, "Working memory should be included"
    
    # Check stats
    assert "short_term_tokens" in stats
    assert "working_memory_tokens" in stats
    assert "total_tokens" in stats
    assert stats["total_tokens"] > 0


def test_cross_session_isolation(memory_manager: MemoryManager) -> None:
    """Test that memories are isolated across different sessions."""
    # Create two sessions
    session_id_1 = f"test_session_1_{uuid.uuid4().hex[:8]}"
    session_id_2 = f"test_session_2_{uuid.uuid4().hex[:8]}"
    
    # Add a memory to session 1
    memory_id_1 = memory_manager.add_memory(
        content="Memory for session 1",
        metadata={"session_specific": True},
        importance=0.7,
        tier=MemoryTier.WORKING,
        session_id=session_id_1
    )
    
    # Add a different memory to session 2
    memory_id_2 = memory_manager.add_memory(
        content="Memory for session 2",
        metadata={"session_specific": True},
        importance=0.7,
        tier=MemoryTier.WORKING,
        session_id=session_id_2
    )
    
    # Memory 1 should be found in session 1
    mem1_in_ses1 = memory_manager.get_memory(memory_id=memory_id_1, session_id=session_id_1)
    assert mem1_in_ses1 is not None
    assert mem1_in_ses1.content == "Memory for session 1"
    
    # Memory 2 should be found in session 2
    mem2_in_ses2 = memory_manager.get_memory(memory_id=memory_id_2, session_id=session_id_2)
    assert mem2_in_ses2 is not None
    assert mem2_in_ses2.content == "Memory for session 2"
    
    # Memory 1 should NOT be found in session 2
    mem1_in_ses2 = memory_manager.get_memory(memory_id=memory_id_1, session_id=session_id_2)
    assert mem1_in_ses2 is None
    
    # Memory 2 should NOT be found in session 1
    mem2_in_ses1 = memory_manager.get_memory(memory_id=memory_id_2, session_id=session_id_1)
    assert mem2_in_ses1 is None


def test_memory_expiration(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test that memories expire after the configured time (needs very short expiry)."""
    # Use Redis store directly to set a very short expiration
    redis_store = memory_manager.redis_store
    original_expiry = redis_store.expire_seconds
    
    try:
        # Set to 1 second for testing
        redis_store.expire_seconds = 1
        
        # Add a memory
        memory_id = memory_manager.add_memory(
            content="This memory will expire quickly",
            metadata={"ephemeral": True},
            importance=0.5,
            tier=MemoryTier.WORKING,
            session_id=unique_session_id
        )
        
        # Verify it exists
        memory = memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id)
        assert memory is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Verify it's gone
        expired_memory = memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id)
        assert expired_memory is None, "Memory should have expired"
        
    finally:
        # Restore original expiry
        redis_store.expire_seconds = original_expiry


def test_delete_memory(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test deleting a memory."""
    # Add a memory
    memory_id = memory_manager.add_memory(
        content="Memory to be deleted",
        metadata={},
        importance=0.5,
        tier=MemoryTier.WORKING,
        session_id=unique_session_id
    )
    
    # Verify it exists
    memory = memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id)
    assert memory is not None
    
    # Delete it
    memory_manager.delete_memory(memory_id=memory_id, tier=MemoryTier.WORKING, session_id=unique_session_id)
    
    # Verify it's gone
    deleted_memory = memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id)
    assert deleted_memory is None, "Memory should have been deleted"


if __name__ == "__main__":
    # Can be run as a script for manual testing
    import pytest
    pytest.main(["-xvs", __file__])
