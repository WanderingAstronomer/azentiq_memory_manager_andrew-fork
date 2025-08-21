#!/usr/bin/env python3
"""
Simple ADK Session test to verify basic functionality
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_adk_session():
    """Test if we can create and use ADK Session"""
    print("\n===== TESTING ADK SESSION =====\n")
    
    try:
        # Import from ADK
        from google.adk.sessions import Session
        from google.genai import types
        
        # Create a simple session
        session_id = f"test-session-{int(datetime.now().timestamp())}"
        session = Session(
            id=session_id,
            app_name="simple-test",
            user_id="test-user"
        )
        
        print(f"Created session with ID: {session_id}")
        print(f"Session type: {type(session)}")
        print(f"Session attributes: {dir(session)}")
        
        # Test session events
        if hasattr(session, 'events'):
            print("\nSession has 'events' attribute")
            print(f"Events type: {type(session.events)}")
            
            # Create a simple event
            try:
                # Create content with Part
                # The method signature is different than expected
                # Let's try creating a Part directly instead
                test_part = types.Part(text="Hello, this is a test message")
                content = types.Content(
                    role="user",
                    parts=[test_part]
                )
                
                # Import Event from the correct module
                from google.adk.events.event import Event
                
                # Create event
                event = Event(
                    author="user",
                    content=content
                )
                
                # Add to session
                session.events.append(event)
                print(f"Added event to session.events: {event}")
                print(f"Session now has {len(session.events)} events")
                
            except Exception as e:
                print(f"Error creating/adding event: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("Session does NOT have 'events' attribute")
            print(f"Available attributes: {dir(session)}")
        
        print("\n===== TEST COMPLETED =====\n")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_adk_session()
