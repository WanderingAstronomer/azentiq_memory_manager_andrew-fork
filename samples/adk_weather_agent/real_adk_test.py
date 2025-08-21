"""
Test script to verify integration with the real Google ADK.
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
logger = logging.getLogger("real_adk_test")

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Azentiq Memory Manager
from core.interfaces import Memory, MemoryTier
from core.memory_manager import MemoryManager
from adapters.adk_adapter import AzentiqAdkMemoryAdapter

# Import from Google ADK
try:
    from google.adk.agent.session import Session
    from google.adk.agent.memory import BaseMemoryService
    HAS_REAL_ADK = True
    logger.info("Using real Google ADK")
except ImportError:
    logger.error("Failed to import Google ADK. Please ensure it's installed correctly.")
    logger.error("You can install it with: pip install google-adk")
    HAS_REAL_ADK = False
    sys.exit(1)


async def test_with_real_adk():
    """Test the Azentiq Memory Manager with real Google ADK."""
    print("\n=== Testing Azentiq Integration with Real Google ADK ===\n")
    
    try:
        # Create in-memory dictionary for the memory manager
        in_memory_dict = {}
        
        # Create memory manager with in-memory store
        memory_manager = MemoryManager(
            redis_url=None,  # Use in-memory fallback
            in_memory_dict=in_memory_dict
        )
        
        # Create ADK adapter with memory manager
        adk_adapter = AzentiqAdkMemoryAdapter(
            memory_manager=memory_manager,
            default_tier=MemoryTier.SHORT_TERM,
            default_importance=0.5,
            default_ttl=3600
        )
        
        # Verify the adapter is a proper ADK BaseMemoryService
        if not isinstance(adk_adapter, BaseMemoryService):
            print("ERROR: Adapter does not properly implement BaseMemoryService!")
            return
        
        print("Step 1: Successfully created ADK adapter with Azentiq MemoryManager")
        
        # Create a real ADK session
        session = Session(session_id="test_real_adk_123", app_name="real_adk_test", user_id="test_user")
        session.add_message("user", "What's the weather in Tokyo?", datetime.now())
        session.add_message("assistant", "The weather in Tokyo is 72°F and sunny.", datetime.now())
        session.add_message("user", "I prefer temperatures in Celsius.", datetime.now())
        session.add_message("assistant", "The weather in Tokyo is 22°C and sunny.", datetime.now())
        
        print(f"Step 2: Created session with {len(session.messages)} messages")
        
        # Add session to memory
        print("Step 3: Adding session to memory...")
        await adk_adapter.add_session_to_memory(session)
        print(f"Session added to memory successfully")
        
        # Search memory
        print("\nStep 4: Searching memory for 'weather'...")
        search_results = await adk_adapter.search_memory("weather", session_id="test_real_adk_123", limit=5)
        
        print(f"Found {len(search_results)} memories related to 'weather':")
        for i, memory in enumerate(search_results):
            print(f"\n{i+1}. Content: {memory['content']}")
            print(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        
        # Search for user preferences
        print("\nStep 5: Searching memory for 'Celsius' (user preference)...")
        preference_results = await adk_adapter.search_memory("Celsius", session_id="test_real_adk_123", limit=5)
        
        print(f"Found {len(preference_results)} memories related to user preference:")
        for i, memory in enumerate(preference_results):
            print(f"\n{i+1}. Content: {memory['content']}")
            print(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        
        print("\n=== Test Complete ===\n")
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())


if __name__ == "__main__":
    if HAS_REAL_ADK:
        asyncio.run(test_with_real_adk())
    else:
        print("Test skipped: Google ADK is not available.")
