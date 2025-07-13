#!/usr/bin/env python3
"""
Demo script for IoT Agent with Memory Manager integration.

This script demonstrates how to:
1. Set up the IoT agent
2. Process simulated telemetry data
3. Query the agent about device history
"""
import os
import sys
import time
import uuid
import getpass
import random
import argparse
from datetime import datetime, timedelta
import json

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the IoT agent class with absolute import
import samples.langchain_iot_agent.iot_agent
from samples.langchain_iot_agent.iot_agent import IoTAgent, generate_simulated_telemetry

def securely_get_api_key():
    """Securely get API key from environment or user input."""
    # First check environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        print("Found OPENAI_API_KEY in environment variables.")
        # Only show first 8 chars and last 4 chars
        if len(api_key) > 12:
            masked_key = f"{api_key[:8]}...{api_key[-4:]}"
            print(f"Using key: {masked_key}")
        return api_key
    
    # If not in environment, get securely from user
    print("\nOPENAI_API_KEY not found in environment variables.")
    print("Please set this environment variable for future runs:")
    print("  Windows PowerShell: $env:OPENAI_API_KEY=\"your-api-key\"")
    print("  Windows CMD: set OPENAI_API_KEY=your-api-key")
    print("  Linux/macOS: export OPENAI_API_KEY=your-api-key")
    print("\nFor this session, you can enter your API key securely:")
    
    try:
        # Try to use getpass for secure input (no echo)
        api_key = getpass.getpass("Enter your OpenAI API key (input will be hidden): ")
    except getpass.GetPassWarning:
        # Fall back to regular input if getpass doesn't work in the environment
        print("Secure input not available. Please enter your API key:")
        api_key = input("Enter your OpenAI API key: ")
        
    if not api_key:
        return None
        
    # Set for current session
    os.environ["OPENAI_API_KEY"] = api_key
    return api_key

def main():
    """Run the IoT agent demo."""
    print("\n=== IoT Agent with Memory Manager Demo ===\n")
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the IoT agent demo")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()
    
    # Securely get API key, first from command-line argument, then from environment or user input
    api_key = args.api_key if args.api_key else securely_get_api_key()
    
    if not api_key:
        print("No API key provided. Exiting demo.")
        return
    
    # Redis URL
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Initialize the IoT agent
    session_id = f"iot_demo_{uuid.uuid4().hex[:8]}"
    print(f"Creating agent with session ID: {session_id}")
    
    agent = IoTAgent(
        session_id=session_id,
        openai_api_key=api_key,
        redis_url=redis_url,
        model_name="gpt-3.5-turbo"
    )
    
    # Define device thresholds
    devices = {
        "temperature_sensor_1": {
            "baseline": {"temperature": 22.0, "humidity": 45.0},
            "variance": {"temperature": 1.0, "humidity": 5.0},
            "thresholds": {
                "temperature": {"min": 18.0, "max": 26.0},
                "humidity": {"min": 30.0, "max": 60.0}
            }
        },
        "pressure_sensor_1": {
            "baseline": {"pressure": 1013.0, "flow_rate": 25.0},
            "variance": {"pressure": 5.0, "flow_rate": 2.0},
            "thresholds": {
                "pressure": {"min": 990.0, "max": 1030.0},
                "flow_rate": {"min": 20.0, "max": 30.0}
            }
        }
    }
    
    # Set thresholds for devices
    for device_id, config in devices.items():
        agent.set_device_thresholds(device_id, config["thresholds"])
    
    print("\nStarting telemetry simulation (press Ctrl+C to stop)...")
    
    # Run telemetry simulation for a limited time in demo
    simulation_count = 0
    total_anomalies = 0
    
    try:
        while simulation_count < 30:  # Limit to 30 readings for demo
            for device_id, config in devices.items():
                # Generate telemetry with 20% chance of anomaly
                telemetry = generate_simulated_telemetry(
                    device_id, 
                    config["baseline"],
                    config["variance"],
                    anomaly_chance=0.2
                )
                
                # Process the telemetry
                anomalies = agent.process_telemetry(device_id, telemetry)
                
                # Print telemetry data
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Device {device_id}")
                for key, value in telemetry.items():
                    print(f"  {key}: {value}")
                
                # Print any anomalies
                if anomalies:
                    total_anomalies += len(anomalies)
                    for anomaly in anomalies:
                        print(f"  ! ANOMALY: {anomaly['description']} (Severity: {anomaly['severity']})")
            
            simulation_count += 1
            
            # Sleep between readings
            time.sleep(1)  # Reduced for demo purposes
    
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    
    print(f"\nProcessed {simulation_count} telemetry readings with {total_anomalies} anomalies detected.")
    
    # Now demonstrate natural language queries
    print("\n=== Query the IoT Agent ===")
    print("Ask questions about the device history or type 'exit' to quit.")
    
    while True:
        question = input("\nEnter your question: ")
        if question.lower() in ["exit", "quit"]:
            break
        
        # Process the query
        print("\nThinking...")
        response = agent.query(question)
        print(f"\nResponse: {response}")
    
    print("\nDemo completed. Memory has been stored in Redis.")
    print(f"Session ID: {session_id}")
    print("You can run the demo again with the same session ID to continue the conversation.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("\nERROR DETAILS:\n")
        print(traceback.format_exc())
        print(f"Exception: {e}\n")
