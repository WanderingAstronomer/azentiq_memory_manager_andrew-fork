#!/usr/bin/env python3
"""
Minimal test for ADK memory integration with Azentiq adapter.
This focuses only on the memory components without requiring the full agent functionality.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Azentiq adapter
from adapters.adk_adapter import AzentiqAdkMemoryAdapter, ADK_AVAILABLE
from core.memory_manager import MemoryManager
from core.interfaces import MemoryTier

async def test_memory_integration():
    """Test basic ADK memory integration with Azentiq."""
    print("\n===== TESTING ADK MEMORY INTEGRATION =====\n")
    
    if not ADK_AVAILABLE:
        logger.error("Google ADK not available. Cannot run test.")
        return False
    
    try:
        # Import ADK Session class
        from google.adk.sessions import Session
        logger.info("Successfully imported ADK Session")
        
        # Create memory adapter with in-memory backend
        adapter = AzentiqAdkMemoryAdapter(
            memory_manager=MemoryManager(in_memory=True),
            default_tier=MemoryTier.SHORT_TERM
        )
        logger.info("Created AzentiqAdkMemoryAdapter with in-memory backend")
        
        # Create an ADK session
        session_id = f"test-session-{datetime.now().timestamp()}"
        session = Session(
            id=session_id,
            app_name="minimal-test",
            user_id="test-user"
        )
        logger.info(f"Created ADK Session with ID: {session_id}")
        
        # Add events to the session
        if hasattr(session, 'events'):
            logger.info("Session has 'events' attribute. Using direct event assignment.")
            
            # Create a simple event - this will depend on ADK's actual API
            try:
                # Try importing Content and Part classes for event creation
                from google.genai.types import Content, Part
                
                # Create Content object
                content = Content(
                    role="user",
                    parts=[Part.from_text("This is a test memory")]
                )
                
                # Create Event object - assuming the actual API structure
                from google.adk.sessions import Event
                event = Event(
                    author="user",
                    content=content
                )
                
                # Add event to session
                session.events.append(event)
                logger.info("Added event to session.events")
                
            except (ImportError, AttributeError) as e:
                logger.error(f"Error creating event: {e}")
                logger.info("Skipping event creation test")
        
        # Store session in memory
        logger.info("Adding session to memory...")
        await adapter.add_session_to_memory(session)
        logger.info("Session added to memory successfully")
        
        # Test memory search
        logger.info("Searching memory...")
        results = await adapter.search_memory("test", session_id=session_id)
        logger.info(f"Found {len(results)} memories")
        
        for i, memory in enumerate(results):
            logger.info(f"Memory {i+1}:")
            logger.info(f"  ID: {memory.get('id')}")
            logger.info(f"  Content: {memory.get('content')}")
            logger.info(f"  Metadata: {memory.get('metadata')}")
        
        print("\n===== TEST COMPLETED SUCCESSFULLY =====\n")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    asyncio.run(test_memory_integration())

if __name__ == "__main__":
    main()
