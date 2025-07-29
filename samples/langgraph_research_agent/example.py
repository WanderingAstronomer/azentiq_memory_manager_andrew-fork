"""
Example script demonstrating the Research Agent with Azentiq Memory Manager.

This script shows how to create and use the ResearchAgent class
to perform research queries and build a knowledge graph over time.
"""

import os
import logging
from research_agent import ResearchAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    Run the research agent example.
    """
    # Check for OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key to run this example.")
        print("Example: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Redis connection string
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # Try to connect to Redis
    import redis
    connected = False
    
    # Try default connection
    try:
        r = redis.Redis.from_url(redis_url)
        if r.ping():
            connected = True
            print(f"Connected to Redis at {redis_url}")
    except:
        print(f"Could not connect to Redis at {redis_url}")
        
    # If default fails, try port 8081 (Redis Commander shows this)
    if not connected:
        try:
            alt_url = "redis://localhost:6379/0"  # This is the likely Redis port even if Commander is on 8081
            r = redis.Redis.from_url(alt_url)
            if r.ping():
                connected = True
                redis_url = alt_url
                print(f"Connected to Redis at {redis_url}")
        except:
            print("Could not connect to alternate Redis port")
            
    # Final fallback - ask user for Redis URL
    if not connected:
        print("\nPlease enter your Redis URL (example: redis://localhost:6379/0):")
        user_url = input("Redis URL: ").strip()
        if user_url:
            redis_url = user_url
    
    print("\n=== Azentiq Memory Manager - LangGraph Research Agent Example ===\n")
    print(f"Connecting to Redis at {redis_url}")
    
    try:
        # Initialize the research agent
        agent = ResearchAgent(
            redis_url=redis_url,
            openai_api_key=openai_api_key
        )
        
        # Example queries to demonstrate knowledge building across queries
        queries = [
            "What is the relationship between LangChain and LangGraph?",
            "How does memory management work in agent systems?",
            "What are the advantages of tiered memory systems?"
        ]
        
        # Run queries one by one
        for i, query in enumerate(queries, 1):
            print(f"\n\n=== Query {i}: {query} ===\n")
            
            # Run the agent
            result = agent.run(query)
            
            # Print the response
            print("\n--- Response ---")
            print(result.get("response", "No response generated"))
            
            # Print entities discovered
            print("\n--- Entities Discovered ---")
            entities = result.get("extracted_entities", [])
            for entity in entities:
                print(f"- {entity['entity']} (Type: {entity['type']})")
            
            # Wait for user to press enter before continuing
            if i < len(queries):
                input("\nPress Enter to continue to next query...")
        
        # Get the knowledge graph after all queries
        print("\n\n=== Final Knowledge Graph ===\n")
        graph = agent.get_knowledge_graph()
        
        print(f"Total Entities: {len(graph['entities'])}")
        print(f"Total Relationships: {len(graph['relationships'])}")
        
        # Print key entities
        print("\nKey Entities:")
        for entity in graph['entities'][:5]:  # Show top 5
            print(f"- {entity['entity']} (Type: {entity['entity_type']})")
        
        # Print key relationships
        if graph['relationships']:
            print("\nKey Relationships:")
            for rel in graph['relationships'][:5]:  # Show top 5
                print(f"- {rel['source']} --> {rel['relationship_type']} --> {rel['target']}")
        
        print("\n=== Example Complete ===")
        
    except Exception as e:
        print(f"Error running example: {e}")

if __name__ == "__main__":
    main()
