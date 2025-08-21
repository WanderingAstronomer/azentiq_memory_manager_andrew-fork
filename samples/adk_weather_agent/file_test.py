"""
Simple test that writes to a file to guarantee output.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Azentiq Memory Manager
try:
    from core.interfaces import Memory, MemoryTier
    from adapters.adk_adapter import AzentiqAdkMemoryAdapter, Session
except Exception as e:
    with open("import_error.log", "w") as f:
        f.write(f"Error importing: {str(e)}\n")
    sys.exit(1)

# Create output file
OUTPUT_FILE = "adapter_test_results.txt"

def write_log(message):
    """Write a message to the output file."""
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


# Mock memory manager for testing
class MockMemoryManager:
    def __init__(self):
        self.memories = {}
        self.component_id = None
        self.session_id = None
        write_log("Mock memory manager initialized")
    
    def set_context(self, component_id, session_id=None):
        """Set the current component context for memory operations."""
        self.component_id = component_id
        self.session_id = session_id
        write_log(f"Context set: component_id={component_id}, session_id={session_id}")
    
    def add_memory(self, content, metadata=None, importance=0.0, memory_id=None, 
                  tier=MemoryTier.WORKING, session_id=None, ttl=None):
        memory_id = memory_id or f"mem_{len(self.memories) + 1}"
        
        # Update metadata with session_id and component_id if available
        metadata = metadata or {}
        if session_id:
            metadata["session_id"] = session_id
        elif self.session_id:
            metadata["session_id"] = self.session_id
            
        if self.component_id:
            metadata["component_id"] = self.component_id
            
        self.memories[memory_id] = Memory(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
            importance=importance,
            tier=tier,
            created_at=datetime.now()
        )
        write_log(f"Added memory: {memory_id} with content: {content[:30]}...")
        return memory_id
    
    def search_by_metadata(self, query, tier=None, limit=10):
        write_log(f"Searching with metadata query: {query}")
        results = []
        for memory_id, memory in self.memories.items():
            # Skip memories not in the specified tier if tier is provided
            if tier and memory.tier != tier:
                continue
                
            matches = True
            for k, v in query.items():
                if k not in memory.metadata or memory.metadata[k] != v:
                    matches = False
                    break
            if matches:
                results.append(memory)
                if len(results) >= limit:
                    break
        write_log(f"Found {len(results)} results in metadata search")
        return results
        
    def search_memories(self, query_text, metadata_filter=None, tier=None, limit=10):
        """Search memories by content text and optional metadata filter."""
        write_log(f"Searching memories with text: '{query_text}', metadata: {metadata_filter}, tier: {tier}")
        
        results = []
        query_text = query_text.lower()
        
        for memory_id, memory in self.memories.items():
            # Skip memories not in the specified tier if tier is provided
            if tier and memory.tier != tier:
                continue
                
            # Check text content match
            if query_text in memory.content.lower():
                # Check metadata filter if provided
                if metadata_filter:
                    matches = True
                    for k, v in metadata_filter.items():
                        if k not in memory.metadata or memory.metadata[k] != v:
                            matches = False
                            break
                    if not matches:
                        continue
                
                results.append(memory)
                if len(results) >= limit:
                    break
                    
        write_log(f"Found {len(results)} results in text search")
        return results


async def test_adk_adapter():
    """Test the ADK adapter integration."""
    # Clear previous output
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    write_log("=== Testing ADK Adapter Integration ===")
    
    try:
        # Create mock memory manager
        memory_manager = MockMemoryManager()
        
        # Create ADK adapter with mock memory manager
        adk_adapter = AzentiqAdkMemoryAdapter(
            memory_manager=memory_manager,
            default_tier=MemoryTier.SHORT_TERM,
            default_importance=0.5,
            default_ttl=3600
        )
        
        write_log("Step 1: Created ADK adapter with mock memory manager")
        
        # Create a session and add messages
        session = Session(session_id="test_session_123", app_name="test_app", user_id="test_user")
        session.add_message("user", "What's the weather in Tokyo?", datetime.now())
        session.add_message("assistant", "The weather in Tokyo is 72°F and sunny.", datetime.now())
        
        write_log("Step 2: Created session with messages")
        
        # Add session to memory
        write_log("Step 3: Adding session to memory...")
        await adk_adapter.add_session_to_memory(session)
        write_log("Session added to memory")
        
        # Search memory
        write_log("Step 4: Searching memory for 'weather'...")
        results = await adk_adapter.search_memory("weather", session_id="test_session_123", limit=5)
        
        write_log(f"Found {len(results)} memories related to 'weather':")
        for i, memory in enumerate(results):
            write_log(f"{i+1}. Content: {memory['content']}")
            write_log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        
        write_log("=== Test Complete ===")
        
    except Exception as e:
        import traceback
        write_log(f"ERROR: {str(e)}")
        write_log(traceback.format_exc())


if __name__ == "__main__":
    try:
        write_log("Starting test...")
        asyncio.run(test_adk_adapter())
        write_log("Test finished.")
    except Exception as e:
        write_log(f"Exception in main: {str(e)}")
        import traceback
        write_log(traceback.format_exc())
