#!/usr/bin/env python3
"""
Minimal test script to diagnose Event creation issues
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def main():
    """Main function to test Event creation"""
    print("=== Minimal Event Creation Test ===")
    
    try:
        # Import required modules
        from google.adk.events.event import Event
        from google.genai import types
        print("Successfully imported Event and types")
        
        # Try minimal Event creation
        event1 = Event(author="user")
        print(f"Successfully created Event with author only: {event1}")
        
        # Try with a Content object
        print("\nCreating Content object...")
        content = types.Content(role="user", parts=[])
        print(f"Content created: {content}")
        
        print("\nCreating Event with content...")
        event2 = Event(author="user", content=content)
        print(f"Successfully created Event with content: {event2}")
        
        # Try with a Content object with a text part
        print("\nCreating Content with Part...")
        content_with_part = types.Content(
            role="user",
            parts=[types.Part.from_text(text="Test message")]
        )
        print(f"Content with Part created: {content_with_part}")
        
        print("\nCreating Event with content with part...")
        event3 = Event(author="user", content=content_with_part)
        print(f"Successfully created Event with content with part: {event3}")
        
        print("\nAll Event creations successful!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("=== Test complete ===")

if __name__ == "__main__":
    main()
