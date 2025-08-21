#!/usr/bin/env python3
"""
Simpler Event debug script to understand the structure of the Event class
"""

import sys
import os
import inspect

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def main():
    """Main function to debug Event class"""
    print("=== Google ADK Event Class Debug ===")
    
    # Import required classes
    try:
        print("Importing modules...")
        from google.adk.events.event import Event
        from google.genai import types
        print("Successfully imported modules")
        
        # Print Event class structure
        print("\nEvent class details:")
        print(f"Event class: {Event}")
        print(f"Event base classes: {Event.__bases__}")
        
        # Print fields and annotations
        print("\nEvent class fields (from __annotations__):")
        if hasattr(Event, "__annotations__"):
            for field, annotation in Event.__annotations__.items():
                print(f"  {field}: {annotation}")
        
        # Check model_config
        if hasattr(Event, "model_config"):
            print("\nEvent.model_config:")
            for key, value in Event.model_config.items():
                print(f"  {key}: {value}")
        
        # Try instantiating with minimal parameters
        print("\nTrying to instantiate Event with minimal parameters...")
        try:
            event = Event(author="user")
            print(f"Success! Event created with author only: {event}")
        except Exception as e:
            print(f"Failed to create Event with author only: {e}")
        
        # Try with Content object
        print("\nTrying to instantiate Event with author and Content...")
        try:
            content = types.Content(
                role="user", 
                parts=[types.Part.from_text(text="Hello")]
            )
            event = Event(author="user", content=content)
            print(f"Success! Event created with author and content")
            print(f"Event: {event}")
            print(f"Event.author: {event.author}")
            print(f"Event.content: {event.content}")
            if event.content and event.content.parts:
                print(f"Event.content.parts[0].text: {event.content.parts[0].text}")
        except Exception as e:
            print(f"Failed to create Event with content: {e}")
            import traceback
            print(traceback.format_exc())
        
    except ImportError as e:
        print(f"Failed to import required modules: {e}")
    
    print("\n=== Debug complete ===")

if __name__ == "__main__":
    main()
