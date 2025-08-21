"""
Test script to verify integration with the real Google ADK with output to file.
"""

import sys
import asyncio
from datetime import datetime
import os
import logging
import traceback

# Define output file
OUTPUT_FILE = "real_adk_test_results.txt"

def write_log(message):
    """Write a message to the output file."""
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

# Clear previous output
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

write_log("Starting Real ADK Integration Test")

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Azentiq Memory Manager
try:
    from core.interfaces import Memory, MemoryTier
    from core.memory_manager import MemoryManager
    from adapters.adk_adapter import AzentiqAdkMemoryAdapter
    write_log("Successfully imported Azentiq Memory Manager components")
except Exception as e:
    write_log(f"ERROR importing Azentiq components: {str(e)}")
    write_log(traceback.format_exc())
    sys.exit(1)

# Import from Google ADK
try:
    from google.adk.agent.session import Session
    from google.adk.agent.memory import BaseMemoryService
    HAS_REAL_ADK = True
    write_log("Successfully imported real Google ADK components")
except ImportError as e:
    write_log(f"Failed to import Google ADK: {str(e)}")
    write_log("Please ensure it's installed correctly. You can install it with: pip install google-adk")
    HAS_REAL_ADK = False
    sys.exit(1)


async def test_with_real_adk():
    """Test the Azentiq Memory Manager with real Google ADK."""
    write_log("=== Testing Azentiq Integration with Real Google ADK ===")
    
    try:
        # Create in-memory dictionary for the memory manager
        in_memory_dict = {}
        
        # Create memory manager with in-memory store
        memory_manager = MemoryManager(
            redis_url=None,  # Use in-memory fallback
            in_memory_dict=in_memory_dict
        )
        write_log("Memory manager created with in-memory store")
        
        # Create ADK adapter with memory manager
        adk_adapter = AzentiqAdkMemoryAdapter(
            memory_manager=memory_manager,
            default_tier=MemoryTier.SHORT_TERM,
            default_importance=0.5,
            default_ttl=3600
        )
        write_log("ADK adapter created with memory manager")
        
        # Verify the adapter is a proper ADK BaseMemoryService
        if not isinstance(adk_adapter, BaseMemoryService):
            write_log("ERROR: Adapter does not properly implement BaseMemoryService!")
            return
        else:
            write_log("Verified: Adapter correctly implements BaseMemoryService")
        
        write_log("Step 1: Successfully created ADK adapter with Azentiq MemoryManager")
        
        # Create a real ADK session
        session = Session(session_id="test_real_adk_123", app_name="real_adk_test", user_id="test_user")
        session.add_message("user", "What's the weather in Tokyo?", datetime.now())
        session.add_message("assistant", "The weather in Tokyo is 72°F and sunny.", datetime.now())
        session.add_message("user", "I prefer temperatures in Celsius.", datetime.now())
        session.add_message("assistant", "The weather in Tokyo is 22°C and sunny.", datetime.now())
        
        write_log(f"Step 2: Created session with {len(session.messages)} messages")
        
        # Add session to memory
        write_log("Step 3: Adding session to memory...")
        await adk_adapter.add_session_to_memory(session)
        write_log(f"Session added to memory successfully")
        
        # Verify memory storage
        memory_count = len(in_memory_dict)
        write_log(f"Verified: {memory_count} memories stored in memory manager")
        
        # Search memory
        write_log("\nStep 4: Searching memory for 'weather'...")
        search_results = await adk_adapter.search_memory("weather", session_id="test_real_adk_123", limit=5)
        
        write_log(f"Found {len(search_results)} memories related to 'weather':")
        for i, memory in enumerate(search_results):
            write_log(f"{i+1}. Content: {memory['content']}")
            write_log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        
        # Search for user preferences
        write_log("\nStep 5: Searching memory for 'Celsius' (user preference)...")
        preference_results = await adk_adapter.search_memory("Celsius", session_id="test_real_adk_123", limit=5)
        
        write_log(f"Found {len(preference_results)} memories related to user preference:")
        for i, memory in enumerate(preference_results):
            write_log(f"{i+1}. Content: {memory['content']}")
            write_log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        
        write_log("=== Test Complete ===")
        return True
    except Exception as e:
        write_log(f"ERROR: {str(e)}")
        write_log(traceback.format_exc())
        return False


if __name__ == "__main__":
    write_log(f"Python version: {sys.version}")
    if HAS_REAL_ADK:
        success = asyncio.run(test_with_real_adk())
        write_log(f"Test {'succeeded' if success else 'failed'}")
    else:
        write_log("Test skipped: Google ADK is not available.")
