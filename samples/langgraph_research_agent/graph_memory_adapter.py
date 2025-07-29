"""
LangGraph Memory Adapter for Azentiq Memory Manager.

This module provides integration between LangGraph and Azentiq Memory Manager
using the event-based architecture and progression templates.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

try:
    from langgraph.graph import StateGraph, Graph
    from langgraph.checkpoint.base import BaseCheckpointSaver
except ImportError:
    raise ImportError(
        "LangGraph not installed. Please install with: pip install langgraph"
    )

from azentiq_memory_manager.tiers import MemoryTier
from azentiq_memory_manager.events import EventBus

logger = logging.getLogger(__name__)

class AzentiqGraphMemory(BaseCheckpointSaver):
    """
    Memory adapter for LangGraph using Azentiq Memory Manager.
    
    This adapter enables LangGraph to store state in tiered memory with
    progression between tiers based on configurable rules.
    """
    
    def __init__(
        self, 
        memory_manager, 
        progression_engine=None,
        template_name: str = "research_assistant",
        session_id: Optional[str] = None,
    ):
        """
        Initialize the LangGraph memory adapter.
        
        Args:
            memory_manager: Azentiq Memory Manager instance
            progression_engine: Optional ProgressionEngine instance
            template_name: Name of progression template to use
            session_id: Optional session identifier
        """
        self.memory_manager = memory_manager
        self.session_id = session_id or self._generate_session_id()
        
        # Set up event bus if not already present
        if not hasattr(memory_manager, 'event_bus'):
            self.event_bus = EventBus()
            memory_manager.set_event_bus(self.event_bus)
        else:
            self.event_bus = memory_manager.event_bus
        
        # Set up progression engine if provided
        self.progression_engine = progression_engine
        if self.progression_engine:
            if template_name:
                self.progression_engine.load_template_by_name(template_name)
            
            # Subscribe progression engine to memory events
            self.event_bus.subscribe("memory_added", self.progression_engine.process_event)
            self.event_bus.subscribe("memory_updated", self.progression_engine.process_event)
        
        logger.info(f"Initialized AzentiqGraphMemory with session_id {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        from uuid import uuid4
        return f"graph_{str(uuid4())}"
    
    def get(self, key: str) -> Dict[str, Any]:
        """
        Get graph state from memory.
        
        Args:
            key: Graph state key
            
        Returns:
            The graph state dictionary
        """
        logger.debug(f"Retrieving graph state for key {key}")
        
        # Search for state memories with this key
        memories = self.memory_manager.search_by_metadata(
            query={
                "type": "graph_state",
                "key": key,
                "session_id": self.session_id
            },
            tier=MemoryTier.SHORT_TERM
        )
        
        if not memories:
            logger.debug(f"No state found for key {key}, returning empty dict")
            return {}
        
        # Sort by timestamp to get the latest
        latest = sorted(
            memories, 
            key=lambda m: m.metadata.get("timestamp", ""), 
            reverse=True
        )[0]
        
        # Parse the JSON content
        try:
            state = json.loads(latest.content)
            logger.debug(f"Retrieved state for key {key}")
            return state
        except json.JSONDecodeError:
            logger.error(f"Failed to parse state JSON for key {key}")
            return {}
    
    def put(self, key: str, state: Dict[str, Any]) -> None:
        """
        Store graph state in memory.
        
        Args:
            key: Graph state key
            state: The graph state to store
        """
        logger.debug(f"Storing graph state for key {key}")
        
        # Convert state to JSON
        try:
            content = json.dumps(state)
        except TypeError:
            logger.error(f"Failed to serialize state for key {key}")
            content = json.dumps({"error": "State serialization failed"})
        
        # Store the state in SHORT_TERM memory
        self.memory_manager.add_memory(
            content=content,
            metadata={
                "type": "graph_state",
                "key": key,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id
            },
            importance=0.7,  # Medium-high importance
            tier=MemoryTier.SHORT_TERM,
            session_id=self.session_id
        )
        
        logger.debug(f"Stored graph state for key {key}")
    
    def add_node_output(
        self, 
        node_name: str, 
        output: Any, 
        importance: float = 0.6
    ) -> str:
        """
        Store output from a graph node.
        
        This allows node results to be stored separately from graph state
        and enables progression rules to process them.
        
        Args:
            node_name: Name of the graph node
            output: Output data from the node
            importance: Importance score (0.0-1.0)
            
        Returns:
            ID of the stored memory
        """
        # Serialize output if needed
        if not isinstance(output, str):
            try:
                content = json.dumps(output)
            except TypeError:
                content = str(output)
        else:
            content = output
        
        # Store the node output
        memory_id = self.memory_manager.add_memory(
            content=content,
            metadata={
                "type": "node_output",
                "node": node_name,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id
            },
            importance=importance,
            tier=MemoryTier.SHORT_TERM,
            session_id=self.session_id
        )
        
        logger.info(f"Stored output from node {node_name} with id {memory_id}")
        return memory_id
    
    def add_entity(self, entity: str, entity_type: str, data: Dict[str, Any]) -> str:
        """
        Store an entity extracted from research.
        
        Entities are stored in WORKING memory to allow knowledge building.
        
        Args:
            entity: Name or identifier of the entity
            entity_type: Type of entity (person, concept, etc.)
            data: Additional entity data
            
        Returns:
            ID of the stored memory
        """
        # Store entity in WORKING memory
        memory_id = self.memory_manager.add_memory(
            content=json.dumps(data),
            metadata={
                "type": "entity",
                "entity": entity,
                "entity_type": entity_type,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id
            },
            importance=0.75,  # Entities have higher importance
            tier=MemoryTier.WORKING,
            session_id=self.session_id
        )
        
        logger.info(f"Stored entity {entity} of type {entity_type}")
        return memory_id
    
    def add_relationship(
        self, 
        source_entity: str, 
        target_entity: str, 
        relationship_type: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Store a relationship between entities.
        
        Args:
            source_entity: Source entity identifier
            target_entity: Target entity identifier
            relationship_type: Type of relationship
            data: Additional relationship data
            
        Returns:
            ID of the stored memory
        """
        # Store relationship in WORKING memory
        memory_id = self.memory_manager.add_memory(
            content=json.dumps(data),
            metadata={
                "type": "relationship",
                "source": source_entity,
                "target": target_entity,
                "relationship_type": relationship_type,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id
            },
            importance=0.7,
            tier=MemoryTier.WORKING,
            session_id=self.session_id
        )
        
        logger.info(f"Stored relationship between {source_entity} and {target_entity}")
        return memory_id
    
    def search_entities(
        self, 
        entity_type: Optional[str] = None, 
        query: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in memory.
        
        Args:
            entity_type: Optional filter by entity type
            query: Additional metadata filters
            
        Returns:
            List of matching entities
        """
        # Build metadata query
        metadata_query = {"type": "entity", "session_id": self.session_id}
        if entity_type:
            metadata_query["entity_type"] = entity_type
        if query:
            metadata_query.update(query)
        
        # Search in WORKING memory
        memories = self.memory_manager.search_by_metadata(
            query=metadata_query,
            tier=MemoryTier.WORKING
        )
        
        # Parse JSON content
        return [
            {
                "id": memory.id,
                "entity": memory.metadata.get("entity"),
                "entity_type": memory.metadata.get("entity_type"),
                "timestamp": memory.metadata.get("timestamp"),
                "data": json.loads(memory.content)
            }
            for memory in memories
        ]
    
    def get_knowledge_graph(self) -> Dict[str, Any]:
        """
        Retrieve the knowledge graph built from entities and relationships.
        
        Returns:
            Dictionary with entities and relationships
        """
        # Get all entities
        entities = self.search_entities()
        
        # Get all relationships
        relationships = self.memory_manager.search_by_metadata(
            query={"type": "relationship", "session_id": self.session_id},
            tier=MemoryTier.WORKING
        )
        
        # Format relationships
        relationship_data = [
            {
                "id": memory.id,
                "source": memory.metadata.get("source"),
                "target": memory.metadata.get("target"),
                "relationship_type": memory.metadata.get("relationship_type"),
                "data": json.loads(memory.content)
            }
            for memory in relationships
        ]
        
        return {
            "entities": entities,
            "relationships": relationship_data
        }
