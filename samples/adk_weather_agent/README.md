# ADK Weather Agent with Azentiq Memory Manager

This sample demonstrates how to integrate Google's Agent Development Kit (ADK) with Azentiq Memory Manager using the AzentiqAdkMemoryAdapter. The example agent provides weather information while remembering user preferences across interactions.

## Features

- **Memory-Aware Weather Agent**: Demonstrates a simple agent that remembers user preferences for locations
- **Google ADK Integration**: Shows how to connect Google ADK with Azentiq Memory Manager
- **Tiered Memory Usage**: Utilizes different memory tiers for conversations vs. user preferences
- **Mock Implementation Support**: Works even without Google ADK installed

## How It Works

The sample implements:

1. A weather agent using Google ADK's Agent framework (or mock equivalent)
2. Integration with Azentiq Memory Manager via the AzentiqAdkMemoryAdapter
3. Automatic storage of conversation history in SHORT_TERM memory
4. Extraction and storage of user preferences in WORKING memory
5. Memory-aware responses that leverage stored preferences

## Memory Architecture

The agent demonstrates Azentiq's tiered memory system:

- **SHORT_TERM Memory**: Stores conversation history (questions and responses about weather)
- **WORKING Memory**: Stores user preferences (like preferred locations) with longer TTL
- **Importance Scoring**: Uses higher importance scores for preferences (0.8) than conversations (0.6)

## Running the Sample

```bash
# Navigate to the project root
cd azentiq_memory_manager

# Make sure Redis is running
# (Redis is required for Azentiq Memory Manager)

# Run the agent demo
python -m samples.adk_weather_agent.adk_weather_agent
```

## Expected Output

The demo runs a simulated conversation showing how the agent:
1. Stores weather queries in memory
2. Extracts location preferences from queries
3. Uses those preferences for future ambiguous queries
4. Can search memories for relevant information

## Extending the Sample

You can extend this sample by:

- Adding a real weather API integration
- Implementing more sophisticated preference extraction
- Adding memory progression rules to move memories between tiers
- Creating a web UI or CLI for interactive chat

## Dependencies

- Azentiq Memory Manager
- Redis
- Google ADK (optional - will use mock classes if not available)

## Note on Google ADK

The sample is designed to work with or without Google ADK installed:

- If Google ADK is installed, it will use the actual ADK Agent framework
- If Google ADK is not installed, it will use mock implementations to demonstrate the concepts
