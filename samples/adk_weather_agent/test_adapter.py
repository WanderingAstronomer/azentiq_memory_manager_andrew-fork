"""
Simple test script to verify ADK adapter functionality.
"""

import sys
import asyncio
from datetime import datetime
import os
import logging

# Configure logging to output to console
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger("adk_test")

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Azentiq Memory Manager
from core.interfaces import Memory, MemoryTier
from adapters.adk_adapter import AzentiqAdkMemoryAdapter, Session

# Mock memory manager for testing without Redis
class MockMemoryManager:
    def __init__(self):
        self.memories = {}
        logger.info("Mock memory manager initialized")
    
    def add_memory(self, content, metadata=None, importance=0.0, memory_id=None, 
                  tier=MemoryTier.WORKING, session_id=None):
        memory_id = memory_id or f"mem_{len(self.memories) + 1}"
        self.memories[memory_id] = Memory(
            memory_id=memory_id,
            content=content,
            metadata=metadata or {},
            importance=importance,
            tier=tier,
            created_at=datetime.now()
        )
        logger.info(f"Added memory: {memory_id} with content: {content[:30]}...")
        return memory_id
    
    def search_by_metadata(self, query, tier=None, limit=10):
        logger.info(f"Searching with query: {query}")
        results = []
        for memory_id, memory in self.memories.items():
            matches = True
            for k, v in query.items():
                if k not in memory.metadata or memory.metadata[k] != v:
                    matches = False
                    break
            if matches:
                results.append(memory)
                if len(results) >= limit:
                    break
        logger.info(f"Found {len(results)} results")
        return results


async def test_adk_adapter():
    """Test the ADK adapter integration."""
    print("\n=== Testing ADK Adapter Integration ===\n")
    
    # Create mock memory manager
    memory_manager = MockMemoryManager()
    
    # Create ADK adapter with mock memory manager
    adk_adapter = AzentiqAdkMemoryAdapter(
        memory_manager=memory_manager,
        default_tier=MemoryTier.SHORT_TERM,
        default_importance=0.5,
        default_ttl=3600
    )
    
    print("Step 1: Created ADK adapter with mock memory manager")
    
    # Create a session and add messages
    session = Session(session_id="test_session_123", app_name="test_app", user_id="test_user")
    session.add_message("user", "What's the weather in Tokyo?", datetime.now())
    session.add_message("assistant", "The weather in Tokyo is 72°F and sunny.", datetime.now())
    
    print("Step 2: Created session with messages")
    
    # Add session to memory
    print("Step 3: Adding session to memory...")
    await adk_adapter.add_session_to_memory(session)
    print("Session added to memory")
    
    # Search memory
    print("\nStep 4: Searching memory for 'weather'...")
    search_results = await adk_adapter.search_memory("weather", user_id="test_user", limit=5)
    
    print(f"Found {len(search_results)} memories related to 'weather':")
    for i, memory in enumerate(search_results):
        print(f"\n{i+1}. Content: {memory['content']}")
        print(f"   Role: {memory['metadata'].get('role', 'unknown')}")
    
    print("\n=== Test Complete ===\n")


if __name__ == "__main__":
    asyncio.run(test_adk_adapter())
