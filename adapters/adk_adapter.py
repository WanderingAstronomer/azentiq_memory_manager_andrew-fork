"""
Google ADK Memory Adapter for Azentiq Memory Manager.

This module provides an implementation of Google Agent Development Kit (ADK)
BaseMemoryService interface using Azentiq Memory Manager as the backend.
"""

from typing import Optional, List, Dict, Any, Union
import asyncio
from abc import ABC, abstractmethod
import logging
from datetime import datetime

# Import Azentiq Memory Manager components
from core.interfaces import Memory, MemoryTier
from core.memory_manager import MemoryManager

# Set up logger
logger = logging.getLogger(__name__)

# Check if Google ADK is available
try:
    # Import paths for Google ADK from GitHub repo structure
    from google.adk.memory import BaseMemoryService
    from google.adk.sessions import Session  # Note: sessions (plural) not session
    ADK_AVAILABLE = True
except ImportError:
    logger.warning("Google ADK not installed. Using mock implementation.")
    ADK_AVAILABLE = False
    
    # Create mock classes if ADK is not available
    class BaseMemoryService(ABC):
        """Mock implementation of Google ADK's BaseMemoryService interface."""
        @abstractmethod
        async def add_session_to_memory(self, session):
            """Add content from a session to memory."""
            pass
                
        @abstractmethod
        async def search_memory(self, query, session_id=None, limit=10):
            """Search for relevant memories."""
            pass
    
    class Session:
        """Mock implementation of Google ADK's Session class."""
        def __init__(self, session_id, app_name, user_id=None):
            self.session_id = session_id
            self.app_name = app_name
            self.user_id = user_id
            self.messages = []
        
        def add_message(self, role, content, timestamp=None):
            """Add a message to the session."""
            self.messages.append({
                "role": role,
                "content": content,
                "timestamp": timestamp or datetime.now()
            })
        
        def get_messages(self):
            """Get all messages in the session."""
            return self.messages


class AzentiqAdkMemoryAdapter(BaseMemoryService):
    """
    Adapter that implements Google ADK's BaseMemoryService interface
    using Azentiq Memory Manager.
    
    This allows Azentiq Memory Manager to be used as a drop-in replacement
    for ADK's memory services in ADK-based agent applications.
    """
    
    def __init__(self, memory_manager=None, redis_url=None, 
                 default_tier=MemoryTier.SHORT_TERM,
                 default_importance=0.5, default_ttl=None):
        """
        Initialize the adapter with an Azentiq Memory Manager.
        
        Args:
            memory_manager: Instance of Azentiq Memory Manager (optional)
            redis_url: Redis URL if memory_manager is not provided
            default_tier: Default memory tier for ADK memories
            default_importance: Default importance score for ADK memories
            default_ttl: Default TTL for ADK memories (in seconds)
        """
        self.memory_manager = memory_manager or MemoryManager(redis_url=redis_url or "redis://localhost:6379/0")
        self.default_tier = default_tier
        self.default_importance = default_importance
        self.default_ttl = default_ttl
        
        # Set component context for memory manager
        self.memory_manager.set_context(component_id="adk_adapter")
        
        logger.info("Initialized AzentiqAdkMemoryAdapter with tier: %s", default_tier)
        
    async def add_session_to_memory(self, session):
        """
        Implements ADK's add_session_to_memory using Azentiq Memory Manager.
        
        Args:
            session: ADK Session object containing messages to store
            
        Returns:
            bool: True if successful
        """
        try:
            # Extract events from the ADK session
            # ADK Session uses 'events' list, not 'messages'
            events = getattr(session, "events", [])
            logger.info(f"Found {len(events)} events in session")
            
            # Get session ID - ADK uses 'id', not 'session_id'
            session_id = getattr(session, "id", getattr(session, "session_id", "unknown_session"))
            logger.info(f"Adding messages from ADK session {session_id} to memory")
            
            # Store each event as an Azentiq memory
            for i, event in enumerate(events):
                # Extract content from event
                # Event object has author and content properties
                author = getattr(event, "author", "unknown")
                event_content = getattr(event, "content", None)
                
                # Extract text from content parts
                if event_content and hasattr(event_content, "parts") and event_content.parts:
                    # Combine all text parts into a single string
                    text_parts = []
                    for part in event_content.parts:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                    content = " ".join(text_parts)
                else:
                    content = str(event_content)
                
                # Get event metadata
                role = getattr(event_content, "role", author) if event_content else author
                timestamp = getattr(event, "timestamp", None)
                
                metadata = {
                    "role": role,
                    "session_id": session_id,  # Use the variable we defined above
                    "app_name": getattr(session, "app_name", "unknown_app"),
                    "adk_source": True,
                    "message_index": i,
                    "adk_timestamp": timestamp
                }
                
                # Add user ID if available
                if hasattr(session, "user_id") and session.user_id:
                    metadata["user_id"] = session.user_id
                
                # Add to Azentiq memory system
                self.memory_manager.add_memory(
                    content=content,
                    metadata=metadata,
                    tier=self.default_tier,
                    importance=self._calculate_importance(content, role),
                    ttl=self.default_ttl
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding session to memory: {str(e)}")
            raise
        
    async def search_memory(self, query, session_id=None, user_id=None, limit=10):
        """
        Implements ADK's search_memory using Azentiq Memory Manager.
        
        Args:
            query: Search query string
            session_id: Optional session ID to filter by
            user_id: Optional user ID to filter by (not used in current implementation)
            limit: Maximum number of results to return
            
        Returns:
            List of memory entries in ADK format
        """
        try:
            logger.info(f"Searching memories with query: '{query}', session_id: {session_id}")
            
            # Build metadata filter
            metadata_filter = {"adk_source": True}
            if session_id:
                metadata_filter["session_id"] = session_id
                
            # Search across multiple tiers
            combined_results = []
            
            # First search SHORT_TERM (recent conversation)
            short_term_results = self.memory_manager.search_memories(
                query_text=query,
                metadata_filter=metadata_filter,
                tier=MemoryTier.SHORT_TERM,
                limit=limit
            )
            combined_results.extend(short_term_results)
            
            # Then search WORKING (if we still need more results)
            if len(combined_results) < limit:
                working_results = self.memory_manager.search_memories(
                    query_text=query,
                    metadata_filter=metadata_filter,
                    tier=MemoryTier.WORKING,
                    limit=limit - len(combined_results)
                )
                combined_results.extend(working_results)
            
            # Finally search LONG_TERM (if we still need more results)
            if len(combined_results) < limit:
                long_term_results = self.memory_manager.search_memories(
                    query_text=query,
                    metadata_filter=metadata_filter,
                    tier=MemoryTier.LONG_TERM,
                    limit=limit - len(combined_results)
                )
                combined_results.extend(long_term_results)
                
            # Format results as ADK memory entries
            adk_results = [self._convert_to_adk_memory(memory) for memory in combined_results]
            
            logger.info(f"Found {len(adk_results)} memories matching query")
            return adk_results
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise
    
    def _calculate_importance(self, content, role):
        """
        Calculate importance score for a message based on content and role.
        
        Args:
            content: Message content
            role: Message role (user, assistant, etc.)
            
        Returns:
            float: Importance score between 0.0 and 1.0
        """
        # Simple heuristic - can be enhanced with more sophisticated analysis
        base_importance = self.default_importance
        
        # Adjust importance based on content length
        if len(content) > 1000:
            base_importance += 0.1  # Longer content may be more important
        
        # Adjust importance based on role
        if role.lower() == "user":
            base_importance += 0.1  # User messages might be more important
        
        # Cap importance between 0.0 and 1.0
        return min(max(base_importance, 0.0), 1.0)
    
    def _convert_to_adk_memory(self, azentiq_memory):
        """
        Convert Azentiq memory to ADK memory entry format.
        
        Args:
            azentiq_memory: Azentiq Memory object
            
        Returns:
            dict: Memory in ADK format
        """
        # Based on ADK's expected memory entry structure
        # This may need adjustment based on ADK's actual implementation
        if not azentiq_memory:
            return None
            
        metadata = azentiq_memory.metadata or {}
        
        adk_memory = {
            "id": azentiq_memory.memory_id,
            "content": azentiq_memory.content,
            "metadata": {
                "role": metadata.get("role", "unknown"),
                "session_id": metadata.get("session_id"),
                "app_name": metadata.get("app_name"),
                "created_at": azentiq_memory.created_at.isoformat() if azentiq_memory.created_at else None
            }
        }
        
        # Add optional fields if available
        if "user_id" in metadata:
            adk_memory["metadata"]["user_id"] = metadata["user_id"]
            
        return adk_memory

# Utility functions for ADK integration

def session_from_azentiq_memories(memories, session_id=None, app_name=None):
    """
    Create an ADK Session from a list of Azentiq memories.
    
    Args:
        memories: List of Azentiq Memory objects
        session_id: Optional session ID (will use from metadata if not provided)
        app_name: Optional app name (will use from metadata if not provided)
        
    Returns:
        Session: ADK Session object
    """
    if not memories:
        return None
        
    # Get session_id and app_name from first memory if not provided
    session_id = session_id or memories[0].metadata.get("session_id", "unknown_session")
    app_name = app_name or memories[0].metadata.get("app_name", "unknown_app")
    
    # Create ADK session
    session = Session(session_id=session_id, app_name=app_name)
    
    # Sort memories by message index or creation time
    sorted_memories = sorted(
        memories,
        key=lambda m: (
            m.metadata.get("message_index", 999999),  # First by message index
            m.created_at or datetime.min  # Then by creation time
        )
    )
    
    # Add messages to session
    for memory in sorted_memories:
        session.add_message(
            role=memory.metadata.get("role", "unknown"),
            content=memory.content,
            timestamp=memory.created_at
        )
    
    return session
