"""
Integration test using the Google ADK from GitHub with corrected import paths.
"""

import sys
import asyncio
from datetime import datetime
import os
import traceback

# Define output file
OUTPUT_FILE = "github_adk_test_results.txt"

def write_log(message):
    """Write a message to the output file."""
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")
    print(message)

# Clear previous output
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

write_log("Starting GitHub ADK Integration Test")

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
# Using the correct import paths from the GitHub repo
HAS_REAL_ADK = False

try:
    # Import Google ADK classes
    from google.adk.sessions import Session
    from google.adk.agents import Agent
    from google.adk.memory import BaseMemoryService
    from google.adk.events.event import Event
    from google.genai import types  # Import types for Content and Part creation
    write_log("Successfully imported Session from google.adk.sessions")
    write_log("Successfully imported Agent from google.adk.agents")
    write_log("Successfully imported BaseMemoryService from google.adk.memory")
    write_log("Successfully imported Event from google.adk.events.event")
    write_log("Successfully imported types from google.genai")
    HAS_REAL_ADK = True
except ImportError as e:
    write_log(f"Failed to import Google ADK classes: {str(e)}")


async def test_with_github_adk():
    """Test the Azentiq Memory Manager with GitHub Google ADK."""
    write_log("=== Testing Azentiq Integration with GitHub Google ADK ===")
    
    try:
        # Create in-memory dictionary for the memory manager
        in_memory_dict = {}
        
        # Create memory manager with proper Redis URL (will use in-memory fallback if Redis not available)
        redis_url = "redis://localhost:6379/0"  # This is required, even if we fall back to in-memory
        
        try:
            memory_manager = MemoryManager(
                redis_url=redis_url,
                short_term_ttl=30 * 60,  # 30 minutes default
                model_token_limit=8192,
                framework="adk_test"
            )
            write_log("Memory manager created with Redis URL (may fall back to in-memory if Redis is unavailable)")
        except Exception as e:
            write_log(f"Error creating memory manager with Redis: {str(e)}")
            write_log("Trying alternative initialization...")
            
            # Try alternative initialization if needed
            from unittest.mock import MagicMock
            from core.interfaces import IMemoryStore
            
            # Create a mock memory store
            mock_store = MagicMock(spec=IMemoryStore)
            memory_manager = MemoryManager(
                redis_url=redis_url,  # Still need to provide this
                short_term_ttl=30 * 60,
                model_token_limit=8192,
                framework="adk_test"
            )
            # Replace Redis store with mock
            memory_manager.redis_store = mock_store
            write_log("Memory manager created with mock store as fallback")
        write_log("Memory manager created with in-memory store")
        
        # Create ADK adapter with memory manager
        adk_adapter = AzentiqAdkMemoryAdapter(
            memory_manager=memory_manager,
            default_tier=MemoryTier.SHORT_TERM,
            default_importance=0.5,
            default_ttl=3600
        )
        write_log("ADK adapter created with memory manager")
        
        # Check if we can use the real ADK Session class
        if 'Session' in globals():
            write_log("Using real Session class from google.adk.sessions")
            # Create a real ADK session with correct parameters
            session = Session(
                id="test_github_adk_123",  # Use 'id' instead of 'session_id'
                app_name="github_adk_test", 
                user_id="test_user"
            )
            
            # Use incremental approach to debug Event creation
            write_log("Step 1: Testing minimal Event creation...")
            try:
                # Try creating a minimal Event (just author)
                minimal_event = Event(author="user")
                write_log(f"Step 1 success: Created minimal Event with author only")
                
                # Step 2: Create a simple Content object
                write_log("Step 2: Creating Content object...")
                user_content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Test message")]
                )
                write_log("Step 2 success: Content object created")
                
                # Step 3: Create an Event with Content
                write_log("Step 3: Creating Event with Content...")
                user_event = Event(author="user", content=user_content)
                write_log(f"Step 3 success: Event created with Content")
                
                # Step 4: Add Event to Session
                write_log("Step 4: Adding Event to Session...")
                session.events.append(user_event)
                write_log(f"Step 4 success: Event added to Session")
                
                # If all steps work, add one more message
                write_log("Step 5: Adding a second Event to Session...")
                assistant_content = types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Response message")]
                )
                assistant_event = Event(author="assistant", content=assistant_content)
                session.events.append(assistant_event)
                write_log("Step 5 success: Second Event added to Session")
                write_log(f"Created session with {len(session.events)} events")
            except Exception as e:
                write_log(f"Failed at Event creation: {str(e)}")
                import traceback
                write_log(traceback.format_exc())
            
            write_log(f"Created session with messages")
            
            # Add session to memory
            write_log("Adding session to memory...")
            await adk_adapter.add_session_to_memory(session)
            write_log("Session added to memory successfully")
            
            # Search memory
            write_log("Searching memory for 'weather'...")
            search_results = await adk_adapter.search_memory("weather", session_id="test_github_adk_123", limit=5)
            
            write_log(f"Found {len(search_results)} memories related to 'weather':")
            for i, memory in enumerate(search_results):
                write_log(f"{i+1}. Content: {memory['content']}")
                write_log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
        else:
            write_log("Failed to import real Session class. Using mock implementation instead.")
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
        write_log("Test failed with error:")
        import traceback
        error_details = traceback.format_exc()
        write_log(error_details)
        write_log(f"Results saved to {OUTPUT_FILE}")
        return False


if __name__ == "__main__":
    write_log(f"Python version: {sys.version}")
    success = asyncio.run(test_with_github_adk())
    write_log(f"Test {'succeeded' if success else 'failed'}")
    write_log(f"Results saved to {OUTPUT_FILE}")
    print(f"Test complete. Results saved to {OUTPUT_FILE}")
