#!/usr/bin/env python3
"""
Minimal Google ADK integration test with Azentiq Memory Manager.
This test focuses solely on correct Event creation and integration.
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Log file for debugging
LOG_FILE = "minimal_adk_test_results.txt"

def write_log(message):
    """Write a timestamped message to the log file"""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {message}\n")

def main():
    """Main function to test Azentiq Memory Manager integration with Google ADK"""
    write_log("Starting Minimal Google ADK Integration Test")
    
    try:
        # Import Azentiq Memory Manager components
        from adapters.adk_adapter import AzentiqADKMemoryAdapter
        from core.memory_manager import MemoryManager
        write_log("Successfully imported Azentiq Memory Manager components")
        
        # Import Google ADK components
        from google.adk.sessions import Session
        write_log("Successfully imported Session from google.adk.sessions")
        
        from google.genai import types
        write_log("Successfully imported types from google.genai")
        
        from google.adk.events.event import Event
        write_log("Successfully imported Event from google.adk.events.event")
        
        # Create a basic in-memory MemoryManager
        memory_manager = MemoryManager(use_redis=False)
        
        # Create adapter with memory manager
        adk_adapter = AzentiqADKMemoryAdapter(memory_manager=memory_manager)
        write_log("Created Azentiq ADK Memory Adapter")
        
        # Create a session using the correct parameters from the source code
        session = Session(
            id="test-session-123",
            app_name="weather-agent",
            user_id="test_user"
        )
        write_log("Created ADK Session")
        
        # Test Event creation with minimal parameters (just author)
        try:
            minimal_event = Event(author="user")
            write_log(f"Created minimal Event with author='user'")
            
            # Test adding minimal event to session
            session.events.append(minimal_event)
            write_log(f"Successfully added minimal Event to Session")
        except Exception as e:
            write_log(f"Failed to create minimal Event: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
            
        # Test Event creation with content
        try:
            # Create a Content object with a single text part
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text("What's the weather like?")]
            )
            write_log(f"Created Content object")
            
            # Create event with content
            user_event = Event(author="user", content=user_content)
            write_log(f"Created Event with Content")
            
            # Add to session
            session.events.append(user_event)
            write_log(f"Successfully added Event with Content to Session")
        except Exception as e:
            write_log(f"Failed to create Event with Content: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
        
        write_log(f"Session now has {len(session.events)} events")
        
        # Test storing memory through the adapter
        try:
            memory_text = "It's sunny in San Francisco."
            metadata = {"source": "weather-service", "location": "San Francisco"}
            
            # Store memory using the adapter
            memory_id = adk_adapter.store(
                text=memory_text,
                session_id="test-session-123", 
                metadata=metadata
            )
            write_log(f"Successfully stored memory with ID: {memory_id}")
            
            # Retrieve memory using the adapter
            results = adk_adapter.search(
                session_id="test-session-123",
                query="weather",
                limit=5
            )
            
            write_log(f"Search returned {len(results)} results")
            for i, result in enumerate(results):
                write_log(f"Result {i+1}: {result.text[:50]}...")
                
        except Exception as e:
            write_log(f"Failed to store/retrieve memory: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
            
        write_log("Test completed successfully")
        
    except Exception as e:
        write_log(f"Test failed: {str(e)}")
        import traceback
        write_log(traceback.format_exc())
    
    write_log("Minimal ADK integration test completed")

if __name__ == "__main__":
    # Create fresh log file
    with open(LOG_FILE, "w") as f:
        f.write("")
    
    main()
