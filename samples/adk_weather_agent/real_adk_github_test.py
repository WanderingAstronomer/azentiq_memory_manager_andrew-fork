"""
Test script to verify integration with Google ADK (GitHub version).
"""

import sys
import asyncio
from datetime import datetime
import os
import traceback

# Define output file
OUTPUT_FILE = "real_adk_github_test_results.txt"

def write_log(message):
    """Write a message to the output file."""
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

# Clear previous output
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

write_log("Starting Real ADK Integration Test (GitHub version)")

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
# Based on GitHub repo, the correct import paths should be:
# from google.adk.agents import Agent  # For agent functionality
# from google.adk.agent.session import Session  # For session functionality
HAS_REAL_ADK = False

# Try different import paths based on GitHub examples
possible_import_paths = [
    # Based on GitHub examples
    {'module': 'google.adk.agents', 'class': 'Agent'},
    {'module': 'google.adk.agent.session', 'class': 'Session'},
    
    # Original paths we tried
    {'module': 'google.adk.agent.session', 'class': 'Session'},
    {'module': 'google.adk.agent.memory', 'class': 'BaseMemoryService'}
]

for import_info in possible_import_paths:
    module_path = import_info['module']
    class_name = import_info['class']
    try:
        write_log(f"Attempting to import {class_name} from {module_path}...")
        module = __import__(module_path, fromlist=[class_name])
        if hasattr(module, class_name):
            write_log(f"✓ Successfully imported {class_name} from {module_path}")
            HAS_REAL_ADK = True
            # Store successful import information
            globals()[class_name] = getattr(module, class_name)
        else:
            write_log(f"✗ Module {module_path} found but does not contain {class_name}")
    except ImportError as e:
        write_log(f"✗ Failed to import {module_path}: {str(e)}")


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
        
        # Check what imports were successful and use appropriate test
        if 'Session' in globals() and 'Agent' in globals():
            write_log("Using Session and Agent classes from real Google ADK")
            # Create a real ADK session using the successfully imported Session class
            session = globals()['Session'](
                session_id="test_real_adk_123", 
                app_name="real_adk_test", 
                user_id="test_user"
            )
            
            # Add messages to session
            session.add_message("user", "What's the weather in Tokyo?", datetime.now())
            session.add_message("assistant", "The weather in Tokyo is 72°F and sunny.", datetime.now())
            session.add_message("user", "I prefer temperatures in Celsius.", datetime.now())
            session.add_message("assistant", "The weather in Tokyo is 22°C and sunny.", datetime.now())
            
            write_log(f"Created session with messages")
            
            # Add session to memory
            write_log("Adding session to memory...")
            await adk_adapter.add_session_to_memory(session)
            write_log("Session added to memory successfully")
            
            # Search memory
            write_log("Searching memory for 'weather'...")
            search_results = await adk_adapter.search_memory("weather", session_id="test_real_adk_123", limit=5)
            
            write_log(f"Found {len(search_results)} memories related to 'weather':")
            for i, memory in enumerate(search_results):
                write_log(f"{i+1}. Content: {memory['content']}")
                write_log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        else:
            write_log("Failed to import required ADK classes. Using mock implementation instead.")
            # Use our mock implementation
            from adapters.adk_adapter import MockSession
            
            session = MockSession(
                session_id="test_mock_adk_123", 
                app_name="mock_adk_test", 
                user_id="test_user"
            )
            
            session.add_message("user", "What's the weather in Tokyo?", datetime.now())
            session.add_message("assistant", "The weather in Tokyo is 72°F and sunny.", datetime.now())
            session.add_message("user", "I prefer temperatures in Celsius.", datetime.now())
            session.add_message("assistant", "The weather in Tokyo is 22°C and sunny.", datetime.now())
            
            write_log(f"Created mock session with messages")
            
            # Add session to memory
            write_log("Adding session to memory...")
            await adk_adapter.add_session_to_memory(session)
            write_log("Session added to memory successfully")
            
            # Search memory
            write_log("Searching memory for 'weather'...")
            search_results = await adk_adapter.search_memory("weather", session_id="test_mock_adk_123", limit=5)
            
            write_log(f"Found {len(search_results)} memories related to 'weather':")
            for i, memory in enumerate(search_results):
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
    success = asyncio.run(test_with_real_adk())
    write_log(f"Test {'succeeded' if success else 'failed'}")
    write_log(f"Results saved to {OUTPUT_FILE}")
    print(f"Test complete. Results saved to {OUTPUT_FILE}")
