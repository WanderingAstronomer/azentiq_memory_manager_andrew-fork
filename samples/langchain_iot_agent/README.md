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

## Setup Instructions

### 1. Install Prerequisites

- Python 3.11 or higher
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Redis)
- OpenAI API key

### 2. Setting up Redis with Docker Desktop

1. **Install Docker Desktop** following the instructions for your operating system from the [Docker website](https://www.docker.com/products/docker-desktop/).

2. **Run Redis container**:
   ```bash
   docker run --name redis-memory-store -p 6379:6379 -d redis
   ```

3. **Verify Redis is running**:
   ```bash
   docker ps
   ```
   You should see the Redis container in the list with status "Up".

### 3. Setting up Redis Commander (Optional)

Redis Commander is a web UI for viewing and interacting with your Redis database:

1. **Run Redis Commander container**:
   ```bash
   docker run --name redis-commander -d --restart always \
   -p 8081:8081 \
   -e REDIS_HOSTS=local:redis-memory-store:6379 \
   --network=host \
   rediscommander/redis-commander
   ```

2. **Access Redis Commander UI**:
   Open your browser and navigate to [http://localhost:8081](http://localhost:8081)

3. **Using Redis Commander**:
   - View all keys in the database
   - Inspect the structure of memory tiers
   - Monitor memory usage in real-time
   - Delete keys or flush the database as needed

### 4. Environment Setup

1. **Install Python dependencies**:
   ```bash
   cd azentiq_memory_manager
   pip install -e .
   pip install -r samples/langchain_iot_agent/requirements.txt
   ```

2. **Set your OpenAI API key**:
   ```bash
   # For Windows PowerShell
   $env:OPENAI_API_KEY="your_api_key"
   
   # For Windows Command Prompt
   set OPENAI_API_KEY=your_api_key
   
   # For Linux/Mac
   export OPENAI_API_KEY=your_api_key
   ```

3. **Configure Redis URL** (optional, defaults to localhost):
   ```bash
   # For Windows PowerShell
   $env:REDIS_URL="redis://localhost:6379/0"
   
   # For Windows Command Prompt
   set REDIS_URL=redis://localhost:6379/0
   
   # For Linux/Mac
   export REDIS_URL=redis://localhost:6379/0
   ```

## Running the Demo

1. **Run the Redis test script** (optional, to verify connectivity):
   ```bash
   cd samples/langchain_iot_agent
   python test_redis.py
   ```

2. **Run the IoT agent demo**:
   ```bash
   cd samples/langchain_iot_agent
   python demo.py
   ```

3. **Interact with the agent**:
   - Wait for initial telemetry data to be processed
   - Enter queries when prompted
   - Press Ctrl+C to exit the simulation

4. **Sample Queries**:
   - "What happened with temperature_sensor_1 in the last few readings?"
   - "Did pressure_sensor_1 show any abnormal patterns?"
   - "What insights have you generated about the sensors?"
   - "Summarize the anomalies detected so far."

5. **View data in Redis Commander** (if installed):
   - Open [http://localhost:8081](http://localhost:8081) in your browser
   - Navigate through the keys to view telemetry, anomalies, and insights
   - Notice the tiered structure with SHORT_TERM and WORKING tiers

## Troubleshooting

1. **Redis Connection Issues**:
   - Verify Docker Desktop is running
   - Check if Redis container is active: `docker ps`
   - Restart Redis if needed: `docker restart redis-memory-store`
   - Verify Redis URL is correct in environment variables

2. **OpenAI API Issues**:
   - Verify your API key is correct and has sufficient credits
   - Check internet connectivity

3. **Data Persistence**:
   - Redis data is not persisted by default in this setup
   - To persist data, modify the Redis Docker command with volume mapping

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
