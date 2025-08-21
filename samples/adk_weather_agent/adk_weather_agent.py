"""
Example weather agent using Google ADK with Azentiq Memory Manager.

This sample demonstrates how to use Azentiq Memory Manager with Google ADK
by creating a simple weather agent that remembers user preferences and
past queries through the Azentiq memory system.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import ADK adapter (with mock ADK if not installed)
from adapters.adk_adapter import AzentiqAdkMemoryAdapter, Session, BaseMemoryService, ADK_AVAILABLE

# Import Azentiq components
from core.interfaces import Memory, MemoryTier
from core.memory_manager import MemoryManager

# Check if actual Google ADK is available
if ADK_AVAILABLE:
    logger.info("Using actual Google ADK")
    # Import additional ADK components
    try:
        # Exact paths based on the ADK repository structure
        from google.adk.tools.tool_configs import ToolConfig
        from google.adk.tools.base_tool import BaseTool as Tool  # Using BaseTool as Tool
        # Import correct Session class from ADK
        from google.adk.sessions.session import Session
        from google.adk.events.event import Event
        from google.genai import types  # Plural 'agents'
    except ImportError as e:
        logger.error(f"Google ADK installed but Agent/Tools modules not found: {e}")
        sys.exit(1)
else:
    logger.warning("Google ADK not installed - using mock implementation")
    
    # Mock ADK components for demonstration
    class ToolConfig:
        def __init__(self, name, args=None):
            self.name = name
            self.args = args or {}

    class Session:
        def __init__(self, id, app_name, user_id):
            self.id = id
            self.app_name = app_name
            self.user_id = user_id
            self.events = []  # Use events list like real ADK
            self.state = {}
            self.last_update_time = datetime.now().timestamp()

    class Event:
        def __init__(self, author=None, content=None):
            self.author = author
            self.content = content
            
    class Part:
        def __init__(self, text=None):
            self.text = text
            
    class Content:
        def __init__(self, role=None, parts=None):
            self.role = role
            self.parts = parts or []
            
    # Mock types module
    types = type('types', (), {'Part': Part, 'Content': Content})
    
    class Agent:
        def __init__(self, tools=None, model="mock-model", memory_service=None):
            self.tools = tools or []
            self.model = model
            self.memory_service = memory_service
            logger.info(f"Initialized mock Agent with {len(tools)} tools")
        
        async def chat(self, session, message):
            """Mock chat method that simulates agent behavior."""
            logger.info(f"Received message: {message}")
            
            if "weather" in message.lower():
                if "tokyo" in message.lower():
                    response = "The weather in Tokyo is 72°F and sunny."
                elif "new york" in message.lower():
                    response = "The weather in New York is 65°F with light rain."
                elif "london" in message.lower():
                    response = "The weather in London is 60°F and cloudy."
                else:
                    response = "I don't have weather information for that location. Try asking about Tokyo, New York, or London."
            else:
                response = "I'm a weather agent. You can ask me about the weather in different cities."
            
            # Store the interaction in memory
            if self.memory_service:
                # Create and add user message event
                user_content = types.Content(
                    role="user",
                    parts=[types.Part(text=message)]
                )
                user_event = Event(
                    author="user",
                    content=user_content
                )
                session.events.append(user_event)
                
                # Create and add assistant response event
                assistant_content = types.Content(
                    role="assistant",
                    parts=[types.Part(text=response)]
                )
                assistant_event = Event(
                    author="assistant",
                    content=assistant_content
                )
                session.events.append(assistant_event)
                
                # Store in memory
                await self.memory_service.add_session_to_memory(session)
            
            return response


class WeatherAgent:
    """Weather agent that uses Google ADK with Azentiq Memory Manager."""
    
    def __init__(self, redis_url="redis://localhost:6379/0", use_mock=False):
        """Initialize the weather agent with memory components."""
        
        try:
            # Initialize Azentiq Memory Manager with Redis backend
            if not use_mock:
                self.memory_manager = MemoryManager(redis_url=redis_url)
                logger.info("Using Redis-backed Memory Manager")
            else:
                raise ValueError("Using mock implementation by request")
        except Exception as e:
            # If Redis connection fails, fall back to a simple in-memory implementation
            logger.warning(f"Redis connection failed or mock requested: {e}. Using in-memory dictionary.")
            from collections import defaultdict
            self.memory_data = {}
            
            # Create a minimal memory manager mock
            class MockMemoryManager:
                def __init__(self, parent):
                    self.parent = parent
                    self.component_id = None

                def set_context(self, component_id=None):
                    """Set the component context for memory operations."""
                    self.component_id = component_id
                    logger.info(f"Set mock memory manager context to: {component_id}")
                    return True

                def add_memory(self, content, metadata=None, importance=0.0, memory_id=None, 
                              tier=None, session_id=None, ttl=None):
                    memory_id = memory_id or f"m_{len(self.parent.memory_data)+1}"
                    memory = Memory(
                        content=content,
                        metadata=metadata or {},
                        memory_id=memory_id,
                        importance=importance,
                        tier=tier or MemoryTier.SHORT_TERM
                    )
                    self.parent.memory_data[memory_id] = memory
                    logger.info(f"Added mock memory: {memory_id}")
                    return memory_id

                def search_by_metadata(self, query, tier=None, limit=10):
                    results = []
                    for memory in self.parent.memory_data.values():
                        # Check if all query key/values are in the memory metadata
                        if all(k in memory.metadata and memory.metadata[k] == v 
                               for k, v in query.items()):
                            results.append(memory)
                            if len(results) >= limit:
                                break
                    return results

                def search_memories(self, query_text=None, query=None, tier=None, limit=10):
                    """Search memories using a text query.
                    
                    Args:
                        query_text: Search query string (preferred parameter name in adapter)
                        query: Alternative parameter name for backwards compatibility
                        tier: Optional tier to filter by
                        limit: Maximum results to return
                    """
                    results = []
                    # Use query_text if provided, otherwise fall back to query
                    search_query = query_text if query_text is not None else query
                    if search_query:
                        # Simple text-based search (case-insensitive)
                        query_lower = search_query.lower()
                        for memory in self.parent.memory_data.values():
                            if query_lower in memory.content.lower():
                                results.append(memory)
                                if len(results) >= limit:
                                    break
                    return results
            
            self.memory_manager = MockMemoryManager(self)
            logger.info("Using in-memory mock for Memory Manager")
        
        # Initialize ADK adapter with Azentiq backend
        self.memory_service = AzentiqAdkMemoryAdapter(
            memory_manager=self.memory_manager,
            default_tier=MemoryTier.SHORT_TERM,  # Recent conversations in SHORT_TERM
            default_importance=0.6,  # Slightly higher importance for weather queries
            default_ttl=3600 * 24  # Store for 24 hours
        )
        
        # Create weather tool for ADK
        # Create weather tool for ADK
        if ADK_AVAILABLE:
            # Use the correct FunctionTool from the ADK
            from google.adk.tools.function_tool import FunctionTool
            
            # Use FunctionTool which is designed for function-based tools
            get_weather_tool = FunctionTool(
                name="get_weather",
                description="Get the current weather for a location",
                function=self._get_weather
            )
        else:
            # Use mock tool implementation
            get_weather_tool = Tool(
                name="get_weather",
                description="Get the current weather for a location",
                function=self._get_weather
            )
        
        # Create ADK agent with our memory service
        self.agent = Agent(
            tools=[get_weather_tool],
            model="gpt-4" if ADK_AVAILABLE else "mock-model",
            memory_service=self.memory_service
        )
        
        logger.info("Weather agent initialized with Azentiq Memory Manager")
    
    async def _get_weather(self, location):
        """Mock weather tool implementation."""
        # This would normally call a weather API
        weather_data = {
            "tokyo": {"temp": 72, "condition": "sunny"},
            "new york": {"temp": 65, "condition": "light rain"},
            "london": {"temp": 60, "condition": "cloudy"},
            "paris": {"temp": 68, "condition": "partly cloudy"},
            "sydney": {"temp": 80, "condition": "sunny"}
        }
        
        location = location.lower()
        if location in weather_data:
            data = weather_data[location]
            return f"The weather in {location.title()} is {data['temp']}°F and {data['condition']}."
        else:
            return f"Weather data for {location} is not available."
    
    async def chat(self, user_id, message):
        """Process user message and return response."""
        # Create or retrieve session
        session_id = f"{user_id}_session"
        app_name = "weather_agent"
        
        # Create new session with correct ADK Session API
        session = Session(
            id=session_id, 
            app_name=app_name, 
            user_id=user_id
        )
        
        # Before responding, check memory for user preferences
        location_pref = await self._get_user_preference(user_id, "preferred_location")
        if location_pref and "weather" in message.lower() and "in" not in message.lower():
            logger.info(f"Using user preference for location: {location_pref}")
            message = f"What's the weather in {location_pref}?"
        
        # Process message with agent
        response = await self.agent.chat(session, message)
        
        # Extract and save preferences from user queries
        await self._extract_preferences(user_id, message, response)
        
        return response
    
    async def _extract_preferences(self, user_id, message, response):
        """Extract and save user preferences from the interaction."""
        # Simple rule-based preference extraction
        if "weather in" in message.lower():
            # Extract location after "weather in"
            parts = message.lower().split("weather in")
            if len(parts) > 1:
                location = parts[1].strip().rstrip("?.,!").strip()
                if location:
                    await self._save_user_preference(user_id, "preferred_location", location)
                    logger.info(f"Saved preferred location '{location}' for user {user_id}")
    
    async def _save_user_preference(self, user_id, pref_key, pref_value):
        """Save user preference to WORKING memory tier."""
        self.memory_manager.add_memory(
            content=pref_value,
            metadata={
                "type": "user_preference",
                "preference_key": pref_key,
                "user_id": user_id
            },
            tier=MemoryTier.WORKING,  # User preferences in WORKING memory
            importance=0.8,  # High importance for preferences
            ttl=3600 * 24 * 30  # Store for 30 days
        )
    
    async def _get_user_preference(self, user_id, pref_key):
        """Retrieve user preference from memory."""
        results = self.memory_manager.search_by_metadata(
            query={
                "type": "user_preference",
                "preference_key": pref_key,
                "user_id": user_id
            },
            tier=MemoryTier.WORKING
        )
        
        if results:
            # Return most recent preference
            return results[0].content
        return None


async def demo():
    """Run a demonstration of the weather agent."""
    print("\n==== Weather Agent with Azentiq Memory Demo ====\n", flush=True)
    # Force flush output after each print
    import sys
    def log(msg):
        print(msg, flush=True)
        sys.stdout.flush()
    
    log("Initializing Weather Agent with mock storage...")
    # Initialize the agent with in-memory mock (no Redis required)
    agent = WeatherAgent(use_mock=True)
    user_id = "demo_user_123"
    log(f"Agent initialized for user: {user_id}")
    
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
    
    log("\n----- Starting conversation simulation -----")
    for i, message in enumerate(conversations):
        log(f"\n[Turn {i+1}/{len(conversations)}]")
        log(f"User: {message}")
        
        try:
            response = await agent.chat(user_id, message)
            log(f"Agent: {response}")
            
            # Check if a preference was saved
            if "Tokyo" in message or "New York" in message or "London" in message:
                location = "Tokyo" if "Tokyo" in message else "New York" if "New York" in message else "London"
                log(f"[System] Attempting to save preference for location: {location}")
            
            # For ambiguous queries, show what's happening
            if message == "What's the weather like today?" or message == "And the weather?":
                log("[System] Using previously stored location preference")
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            import traceback
            log(traceback.format_exc())
        
        # Pause for readability
        await asyncio.sleep(0.5)
    
    # Demonstrate memory search
    log("\n\n==== Memory Search Demo ====\n")
    
    try:
        # Search memory for weather-related content
        log("Searching memories for 'weather'...")
        results = await agent.memory_service.search_memory("weather", user_id=user_id, limit=5)
        
        log(f"Found {len(results)} memories related to 'weather':")
        for i, memory in enumerate(results):
            log(f"\n{i+1}. Content: {memory['content']}")
            log(f"   Role: {memory['metadata'].get('role', 'unknown')}")
            log(f"   Created: {memory['metadata'].get('created_at')}")
    except Exception as e:
        log(f"Error during memory search: {str(e)}")
        import traceback
        log(traceback.format_exc())
    
    log("\n==== Demo Completed ====\n")


if __name__ == "__main__":
    asyncio.run(demo())
