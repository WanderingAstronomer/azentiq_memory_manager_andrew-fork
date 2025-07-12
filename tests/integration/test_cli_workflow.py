"""Integration tests focusing on the CLI demo functionality.

This test file simulates the workflows that would occur in the CLI demo,
testing the Memory Manager's ability to store and retrieve session memories via Redis.
"""

import pytest
from typing import Dict, List

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.interfaces import Memory, MemoryTier
from memory_manager import MemoryManager


@pytest.mark.integration
def test_cli_conversation_workflow(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test a complete CLI conversation workflow with memory persistence.
    
    This simulates a CLI demo conversation where:
    1. User asks questions
    2. System stores conversation turns
    3. System retrieves relevant context from working memory
    4. System generates prompts with combined memory
    """
    # Step 1: Set up some initial knowledge in working memory
    knowledge_memory_ids = []
    
    # Add facts to working memory
    knowledge_entries = [
        {
            "content": "Redis is an in-memory data structure store, used as a database, cache, and message broker.",
            "metadata": {"topic": "redis", "type": "definition"}
        },
        {
            "content": "Python can connect to Redis using the redis-py client library.",
            "metadata": {"topic": "redis", "type": "usage", "language": "python"}
        },
        {
            "content": "LangChain is a framework for developing applications powered by language models.",
            "metadata": {"topic": "langchain", "type": "definition"}
        }
    ]
    
    for entry in knowledge_entries:
        memory_id = memory_manager.add_memory(
            content=entry["content"],
            metadata=entry["metadata"],
            importance=0.8,
            tier=MemoryTier.WORKING,
            session_id=unique_session_id
        )
        knowledge_memory_ids.append(memory_id)
    
    # Step 2: Simulate a conversation (multiple turns)
    conversation = [
        {"role": "user", "content": "What is Redis?"},
        {"role": "assistant", "content": "Redis is an in-memory data structure store. It's commonly used as a database, cache, or message broker."},
        {"role": "user", "content": "Can I use it with Python?"},
        {"role": "assistant", "content": "Yes, you can use Redis with Python. The most popular client library is redis-py."},
        {"role": "user", "content": "Tell me about LangChain."}
    ]
    
    # Add conversation turns to short-term memory
    for i, turn in enumerate(conversation):
        memory_manager.add_memory(
            content=turn["content"],
            metadata={"role": turn["role"], "turn": i},
            importance=1.0,
            tier=MemoryTier.SHORT_TERM,
            session_id=unique_session_id
        )
    
    # Step 3: Generate a prompt for the last user query
    system_message = "You are a helpful assistant with knowledge about databases and AI frameworks."
    user_query = conversation[-1]["content"]  # "Tell me about LangChain"
    
    prompt, stats = memory_manager.generate_prompt(
        session_id=unique_session_id,
        system_message=system_message,
        user_query=user_query,
        max_short_term_turns=4,  # Get the recent conversation context
        include_working_memory=True  # Include relevant facts from working memory
    )
    
    # Verify prompt contents
    assert system_message in prompt, "System message should be included in the prompt"
    assert "Redis is an in-memory data structure store" in prompt, "Conversation context should be included"
    assert "Can I use it with Python?" in prompt, "User questions should be included"
    assert "LangChain is a framework" in prompt, "Relevant working memory should be included"
    
    # Verify token stats are tracked
    assert stats["total_tokens"] > 0, "Token statistics should be tracked"
    assert stats["short_term_tokens"] > 0, "Short-term memory tokens should be counted"
    assert stats["working_memory_tokens"] > 0, "Working memory tokens should be counted"
    
    # Step 4: Test memory persistence by checking if conversation history remains
    all_short_term = memory_manager.search_by_metadata(
        query={"role": "user"},
        tier=MemoryTier.SHORT_TERM,
        limit=10
    )
    
    user_turns = [m for m in all_short_term if m.metadata.get("role") == "user"]
    assert len(user_turns) == 3, "All user turns should be persisted in short-term memory"
    
    # Verify the working memory can be searched by topic
    redis_facts = memory_manager.search_by_metadata(
        query={"topic": "redis"},
        tier=MemoryTier.WORKING,
        limit=5
    )
    assert len(redis_facts) == 2, "Should find two facts about Redis"
    
    # Step 5: Clean up
    # This is handled by the fixture, but we can verify deletion works
    for memory_id in knowledge_memory_ids:
        memory_manager.delete_memory(
            memory_id=memory_id,
            tier=MemoryTier.WORKING,
            session_id=unique_session_id
        )
        
        # Verify deletion worked
        assert memory_manager.get_memory(memory_id=memory_id, session_id=unique_session_id) is None, \
            "Memory should be deleted"


@pytest.mark.integration
def test_memory_retrieval_with_feedback(memory_manager: MemoryManager, unique_session_id: str) -> None:
    """Test memory retrieval with importance-based selection and feedback loop.
    
    This simulates a scenario where:
    1. Multiple memories are added with different importance scores
    2. Memories are retrieved based on relevance and importance
    3. Feedback from the user/system updates importance scores
    """
    # Add several memories with varying importance
    memories = [
        {
            "content": "Redis SETEX command sets both a key's value and its expiration in a single atomic operation.",
            "metadata": {"topic": "redis", "command": "SETEX"},
            "importance": 0.5
        },
        {
            "content": "Redis persistence options include RDB snapshots and AOF logs.",
            "metadata": {"topic": "redis", "subtopic": "persistence"},
            "importance": 0.7
        },
        {
            "content": "Redis Cluster provides high availability through automatic partitioning and replication.",
            "metadata": {"topic": "redis", "subtopic": "clustering"},
            "importance": 0.9
        }
    ]
    
    memory_ids = []
    for mem in memories:
        memory_id = memory_manager.add_memory(
            content=mem["content"],
            metadata=mem["metadata"],
            importance=mem["importance"],
            tier=MemoryTier.WORKING,
            session_id=unique_session_id
        )
        memory_ids.append(memory_id)
    
    # Test retrieving all memories about Redis
    redis_memories = memory_manager.search_by_metadata(
        query={"topic": "redis"},
        tier=MemoryTier.WORKING,
        limit=10
    )
    
    assert len(redis_memories) == 3, "Should find all Redis memories"
    
    # Test retrieving memories with high importance (simulating memory selection strategy)
    # In a real implementation, this would be done via the token budget manager's selection strategy
    high_importance_memories = [m for m in redis_memories if m.importance >= 0.7]
    assert len(high_importance_memories) == 2, "Should find 2 high-importance memories"
    
    # Simulate feedback loop: update importance based on user interaction
    # (e.g., user found persistence information more useful)
    persistence_memory = next(m for m in redis_memories if "persistence" in m.metadata.get("subtopic", ""))
    persistence_memory.importance = 0.95  # Increase importance based on feedback
    
    # Update the memory
    memory_manager.update_memory(persistence_memory, session_id=unique_session_id)
    
    # Verify the importance was updated
    updated_memory = memory_manager.get_memory(
        memory_id=persistence_memory.memory_id,
        session_id=unique_session_id
    )
    
    assert updated_memory.importance == 0.95, "Importance should be updated after feedback"
    
    # Generate prompt with updated importance values (would affect selection in real implementation)
    system_message = "You are a Redis expert."
    user_query = "Tell me about Redis persistence options."
    
    prompt, _ = memory_manager.generate_prompt(
        session_id=unique_session_id,
        system_message=system_message,
        user_query=user_query,
        include_working_memory=True
    )
    
    # The persistence information should be included due to high importance and relevance
    assert "RDB snapshots and AOF logs" in prompt, "High-importance relevant memory should be in prompt"
