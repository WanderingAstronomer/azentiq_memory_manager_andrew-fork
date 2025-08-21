#!/usr/bin/env python3
"""
Simple runner script for weather agent demo
"""

import os
import sys
import asyncio
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the weather agent
from adk_weather_agent import WeatherAgent, demo

def main():
    """Run the weather agent demo with clear console output"""
    print("\n===== STARTING WEATHER AGENT DEMO =====\n")
    time.sleep(1)  # Brief pause for visibility
    
    # Run the async demo
    asyncio.run(demo())
    
    print("\n===== DEMO COMPLETED =====\n")
    print("Press Enter to exit...")
    input()  # Wait for user input before closing

if __name__ == "__main__":
    main()
