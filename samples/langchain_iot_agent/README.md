# LangChain IoT Agent with Azentiq Memory Manager

This sample demonstrates how to integrate the Azentiq Memory Manager with LangChain to create an IoT monitoring agent that can process telemetry data, detect anomalies, and answer natural language queries about device history.

## Features

- **Real-time Telemetry Processing**: Processes IoT device readings every 10 seconds
- **Anomaly Detection**: Identifies readings outside normal thresholds
- **Pattern Recognition**: Detects trends across multiple readings
- **Memory Tiers**: Uses Redis-backed memory tiers
  - Short-term memory for raw telemetry
  - Working memory for anomalies and insights
- **Natural Language Interface**: Ask questions about device history

## Components

### 1. Memory Adapter (`memory_adapter.py`)

A custom LangChain memory implementation that integrates with Azentiq Memory Manager. This adapter:

- Translates between LangChain message formats and Memory Manager format
- Stores conversation history in short-term memory
- Provides methods to store telemetry, anomalies, and insights
- Handles retrieval of relevant context for natural language queries

### 2. IoT Agent (`iot_agent.py`)

The main agent implementation that:

- Processes incoming telemetry data
- Detects anomalies based on configurable thresholds
- Identifies patterns and trends in device readings
- Generates insights about detected anomalies using LLM
- Answers natural language queries about device history

### 3. Demo Script (`demo.py`)

A demonstration script that:

- Sets up the IoT agent
- Simulates telemetry data from multiple devices
- Processes the data in real-time
- Allows you to ask questions about device history

## Memory Tier Usage

This example demonstrates the progression of memory through tiers:

1. **Short-term Memory (Redis)**:
   - Raw telemetry readings
   - Conversation history
   - Very recent device state

2. **Working Memory (Redis)**:
   - Detected anomalies
   - Generated insights
   - Device thresholds and configuration
   - Pattern/trend analysis

## Running the Sample

1. **Prerequisites**:
   - Python 3.11+
   - Redis instance running
   - OpenAI API key

2. **Environment Setup**:
   ```
   # Set your OpenAI API key
   export OPENAI_API_KEY=your_api_key
   
   # Configure Redis (defaults to localhost)
   export REDIS_URL=redis://localhost:6379/0
   ```

3. **Run the Demo**:
   ```
   cd samples/langchain_iot_agent
   python demo.py
   ```

4. **Sample Queries**:
   - "What happened with temperature_sensor_1 in the last few readings?"
   - "Did pressure_sensor_1 show any abnormal patterns?"
   - "What insights have you generated about the sensors?"
   - "Summarize the anomalies detected so far."

## Extending the Sample

This sample can be extended in several ways:

1. **Add more device types** with different metrics and thresholds
2. **Implement more sophisticated anomaly detection** algorithms
3. **Add visualization** of device data and anomalies
4. **Connect to real IoT devices** instead of simulation
5. **Implement feedback loop** to improve anomaly detection over time

## Integration with Memory Manager

This sample showcases how the Azentiq Memory Manager can be used as a library to provide sophisticated memory capabilities to a LangChain agent. Key integration points include:

- Using the Memory Manager to store and retrieve device telemetry
- Leveraging memory tiers for different types of information
- Using metadata for efficient filtering and searching
- Importance scoring for prioritizing critical information
