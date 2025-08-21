#!/usr/bin/env python3
"""
Event Test Script - Focused test to understand Google ADK Event class requirements
"""

import sys
import os
import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Output file for logs
OUTPUT_FILE = "../../event_test_results.txt"

def write_log(message):
    """Write log message to both console and file"""
    timestamp = datetime.datetime.now().isoformat()
    full_message = f"{timestamp} - {message}"
    print(full_message)
    
    # Also write to file
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def main():
    """Main test function"""
    # Clear previous results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("")
    
    write_log("Starting Event Test")
    
    try:
        # Import the required modules
        write_log("Importing Google ADK modules...")
        from google.adk.events.event import Event
        from google.genai import types
        write_log("Successfully imported Event from google.adk.events.event")
        write_log("Successfully imported types from google.genai")
        
        # Try creating Event objects
        write_log("\n==== Test 1: Create Event with simple Content object ====")
        try:
            write_log("Creating Content object with role and text part...")
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text="Hello, world!")]
            )
            write_log(f"Content object created: {repr(content)}")
            
            write_log("Creating Event object with author and content...")
            event = Event(author="user", content=content)
            write_log(f"Event successfully created: {repr(event)}")
            write_log("Test 1 Passed!")
        except Exception as e:
            write_log(f"Test 1 Failed: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
        
        # Try creating event with different parameters
        write_log("\n==== Test 2: Create Event with minimal required parameters ====")
        try:
            write_log("Creating Event with only author (required)...")
            event = Event(author="user")
            write_log(f"Event created: {repr(event)}")
            write_log("Test 2 Passed!")
        except Exception as e:
            write_log(f"Test 2 Failed: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
        
        # Try to create event with string content (which shouldn't work)
        write_log("\n==== Test 3: Create Event with string content (should fail) ====")
        try:
            write_log("Creating Event with string content...")
            event = Event(author="user", content="Hello, world!")
            write_log(f"Event created (unexpected): {repr(event)}")
            write_log("Test 3 Passed (unexpected!)")
        except Exception as e:
            write_log(f"Test 3 Failed as expected: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
        
        # Try to print verbose information about Event class
        write_log("\n==== Test 4: Inspect Event class ====")
        try:
            write_log(f"Event class: {Event}")
            write_log(f"Event class __init__ signature: {Event.__init__.__annotations__ if hasattr(Event.__init__, '__annotations__') else 'Not available'}")
            write_log(f"Event class fields: {[f for f in dir(Event) if not f.startswith('_')]}")
            
            # Create a minimal valid event and inspect it
            minimal_event = Event(author="user")
            write_log(f"Minimal event attributes: {minimal_event.__dict__}")
            write_log("Test 4 Passed!")
        except Exception as e:
            write_log(f"Test 4 Failed: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
        
        write_log("\n==== All tests complete! ====")
        
    except Exception as e:
        write_log("Error in main test function:")
        import traceback
        write_log(traceback.format_exc())
    
    write_log(f"Results saved to {OUTPUT_FILE}")
    return True

if __name__ == "__main__":
    main()
