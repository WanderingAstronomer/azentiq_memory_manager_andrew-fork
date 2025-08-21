#!/usr/bin/env python3
"""
Minimal ADK Memory Adapter Test

This script focuses on testing the core adapter functionality that connects
Google ADK memory capabilities with Azentiq Memory Manager.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Azentiq components
from core.interfaces import Memory
from adapters.adk_adapter import AzentiqAdkMemoryAdapter, MemoryTier

# Import Google ADK components
try:
    # Try importing actual ADK components
    from google.adk.sessions.session import Session
    from google.adk.events.event import Event
    from google.genai import types
    ADK_AVAILABLE = True
    logger.info("Using actual Google ADK")
except ImportError as e:
    logger.warning(f"Google ADK not available: {e}")
    ADK_AVAILABLE = False
    # Create mock types for testing without actual ADK
    class Session:
        def __init__(self, id, app_name, user_id):
            self.id = id
            self.app_name = app_name
            self.user_id = user_id
            self.events = []
            self.state = {}
            self.last_update_time = datetime.now().timestamp()
    
    class Event:
        def __init__(self, author=None, content=None):
            self.author = author
            self.content = content
            self.id = f"mock-event-{datetime.now().timestamp()}"
    
    class Part:
        def __init__(self, text=None):
            self.text = text
            
    class Content:
        def __init__(self, role=None, parts=None):
            self.role = role
            self.parts = parts or []
            
    # Mock types module
    types = type('types', (), {'Part': Part, 'Content': Content})


async def test_adk_memory_adapter():
    """Test the ADK Memory Adapter with basic functionality"""
    print("\n===== TESTING ADK MEMORY ADAPTER =====\n")
    
    try:
        # Initialize mock memory components
        print("Initializing mock memory components...")
        
        # Mock Memory Manager implementation
        class MockMemoryManager:
            def __init__(self):
                self.memory_data = {}
                self.component_id = None
                
            def set_context(self, component_id):
                self.component_id = component_id
                print(f"Set mock memory manager context to: {component_id}")
                return True
                
            def add_memory(self, content, metadata=None, importance=0.0, memory_id=None, 
                          tier=None, session_id=None, ttl=None):
                memory_id = memory_id or f"m_{len(self.memory_data)+1}"
                memory = Memory(
                    content=content,
                    metadata=metadata or {},
                    memory_id=memory_id,
                    importance=importance,
                    created_at=datetime.now()
                )
                self.memory_data[memory_id] = memory
                print(f"Added memory with ID: {memory_id}")
                return memory
                
            def search_memories(self, query_text=None, limit=10, metadata_filter=None, query=None, tier=None):
                # tier parameter is accepted but ignored in this mock implementation
                print(f"Searching for: {query_text} with filter: {metadata_filter}")
                results = []
                
                # Simple text-based search (case-insensitive)
                if query_text:
                    query_lower = query_text.lower()
                    for memory in self.memory_data.values():
                        if query_lower in memory.content.lower():
                            # Apply metadata filter if provided
                            if metadata_filter:
                                match = True
                                for k, v in metadata_filter.items():
                                    if k not in memory.metadata or memory.metadata[k] != v:
                                        match = False
                                        break
                                if match:
                                    results.append(memory)
                            else:
                                results.append(memory)
                            
                            if len(results) >= limit:
                                break
                return results
                
        memory_manager = MockMemoryManager()
        memory_manager.set_context("adk_adapter_test")
        
        # Create ADK adapter with Azentiq backend
        print("Creating ADK Memory Adapter...")
        adapter = AzentiqAdkMemoryAdapter(
            memory_manager=memory_manager,
            default_tier=MemoryTier.SHORT_TERM,
            default_importance=0.5,
            default_ttl=3600  # 1 hour TTL
        )
        
        # Create a session
        session_id = f"test-session-{int(datetime.now().timestamp())}"
        session = Session(
            id=session_id,
            app_name="adapter-test",
            user_id="test-user"
        )
        print(f"Created session with ID: {session_id}")
        
        # Test 1: Add user message to session
        print("\nTest 1: Adding user message to session...")
        user_content = types.Content(
            role="user",
            parts=[types.Part(text="Hello, this is a test message")]
        )
        user_event = Event(
            author="user",
            content=user_content
        )
        session.events.append(user_event)
        print(f"Added user event to session (event ID: {getattr(user_event, 'id', 'unknown')})")
        
        # Test 2: Add assistant message to session
        print("\nTest 2: Adding assistant message to session...")
        assistant_content = types.Content(
            role="assistant",
            parts=[types.Part(text="Hello! I'm here to help with your test.")]
        )
        assistant_event = Event(
            author="assistant",
            content=assistant_content
        )
        session.events.append(assistant_event)
        print(f"Added assistant event to session (event ID: {getattr(assistant_event, 'id', 'unknown')})")
        
        # Test 3: Store session in memory
        print("\nTest 3: Storing session in memory...")
        await adapter.add_session_to_memory(session)
        print("Session stored in memory")
        
        # Test 4: Search for memories
        print("\nTest 4: Searching for memories...")
        results = await adapter.search_memory("test message", session_id=session_id, limit=5)
        print(f"Found {len(results)} memories related to 'test message'")
        for i, memory in enumerate(results):
            print(f"\n{i+1}. Content: {memory.get('content', 'No content')}")
            metadata = memory.get('metadata', {})
            print(f"   Role: {metadata.get('role', 'unknown')}")
            print(f"   Author: {metadata.get('author', 'unknown')}")
            if 'created_at' in metadata:
                print(f"   Created: {metadata['created_at']}")
            
        # Test 5: Update an existing memory with addendum
        print("\nTest 5: Adding more content to session...")
        # Add another event
        followup_content = types.Content(
            role="user",
            parts=[types.Part(text="Can you search for weather information?")]
        )
        followup_event = Event(
            author="user",
            content=followup_content
        )
        session.events.append(followup_event)
        
        # Store updated session
        await adapter.add_session_to_memory(session)
        print("Updated session stored in memory")
        
        # Test 6: Search for new content
        print("\nTest 6: Searching for new content...")
        results = await adapter.search_memory("weather", session_id=session_id, limit=5)
        print(f"Found {len(results)} memories related to 'weather'")
        for i, memory in enumerate(results):
            print(f"\n{i+1}. Content: {memory.get('content', 'No content')}")
            metadata = memory.get('metadata', {})
            print(f"   Role: {metadata.get('role', 'unknown')}")
            print(f"   Author: {metadata.get('author', 'unknown')}")
        
        print("\n===== TEST COMPLETED SUCCESSFULLY =====")
        return True
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_adk_memory_adapter())
