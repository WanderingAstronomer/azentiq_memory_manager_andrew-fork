#!/usr/bin/env python3
"""
Weather agent demo with file-based logging
"""

import os
import sys
import asyncio
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the weather agent
from adk_weather_agent import WeatherAgent

# Log file path
LOG_FILE = os.path.join(os.path.dirname(__file__), "weather_demo_log.txt")

def write_log(message):
    """Write a message to the log file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    
    # Also print to console with flush
    print(message, flush=True)

async def file_log_demo():
    """Run the weather agent demo with file-based logging"""
    # Create or clear the log file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Weather Agent Demo Log - Started at {datetime.now()}\n\n")
    
    write_log("===== WEATHER AGENT DEMO STARTED =====")
    
    try:
        # Initialize the agent with in-memory mock (no Redis required)
        write_log("Initializing Weather Agent with mock storage...")
        agent = WeatherAgent(use_mock=True)
        user_id = "demo_user_123"
        write_log(f"Agent initialized for user: {user_id}")
        
        # Simulate conversation
        conversations = [
            "Hi, can you help me with weather information?",
            "What's the weather in Tokyo?",
            "How about New York?",
            "Thanks!",
            "What's the weather like today?",  # Should use Tokyo preference
            "What about London's weather?",
            "And the weather?",  # Should use London preference
        ]
        
        write_log("----- Starting conversation simulation -----")
        for i, message in enumerate(conversations):
            write_log(f"\n[Turn {i+1}/{len(conversations)}]")
            write_log(f"User: {message}")
            
            try:
                response = await agent.chat(user_id, message)
                write_log(f"Agent: {response}")
                
                # Check if a preference was saved
                if "Tokyo" in message or "New York" in message or "London" in message:
                    location = "Tokyo" if "Tokyo" in message else "New York" if "New York" in message else "London"
                    write_log(f"[System] Attempting to save preference for location: {location}")
                
                # For ambiguous queries, show what's happening
                if message == "What's the weather like today?" or message == "And the weather?":
                    write_log("[System] Using previously stored location preference")
                
            except Exception as e:
                write_log(f"ERROR: {str(e)}")
                import traceback
                write_log(traceback.format_exc())
            
            # Pause for readability
            await asyncio.sleep(0.5)
        
        # Demonstrate memory search
        write_log("\n\n===== MEMORY SEARCH DEMO =====\n")
        
        try:
            # Search memory for weather-related content
            write_log("Searching memories for 'weather'...")
            # Update the search_memory call to handle user_id parameter correctly
            results = await agent.memory_service.search_memory("weather", session_id=None, user_id=user_id, limit=5)
            
            write_log(f"Found {len(results)} memories related to 'weather':")
            for i, memory in enumerate(results):
                write_log(f"\n{i+1}. Content: {memory['content']}")
                write_log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
                write_log(f"   Created: {memory['metadata'].get('created_at')}")
        except Exception as e:
            write_log(f"Error during memory search: {str(e)}")
            import traceback
            write_log(traceback.format_exc())
        
        write_log("\n===== DEMO COMPLETED =====")
        
    except Exception as e:
        write_log(f"Demo failed with error: {str(e)}")
        import traceback
        write_log(traceback.format_exc())
    
    write_log(f"\nLog file created at: {os.path.abspath(LOG_FILE)}")

def main():
    """Main function to run the demo"""
    print(f"Starting weather agent demo with logging to {LOG_FILE}", flush=True)
    asyncio.run(file_log_demo())
    print(f"\nDemo completed. Log available at: {os.path.abspath(LOG_FILE)}", flush=True)

if __name__ == "__main__":
    main()
