"""Memory Adapter for LangChain Integration with Azentiq Memory Manager.

This module provides memory adapter classes for integrating LangChain with
Azentiq Memory Manager, enabling tiered memory persistence in Redis.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union
import json
import logging
from uuid import uuid4
from datetime import datetime

# Configure logging
logger = logging.getLogger('memory_adapter')

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.memory.chat_memory import BaseChatMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain.memory.chat_memory import BaseChatMemory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Import Pydantic for model definition
from pydantic import Field, PrivateAttr

# Import Azentiq Memory Manager components
from core.interfaces import MemoryTier
from core.memory_manager import MemoryManager

class AzentiqMemory(BaseChatMemory):
    """Memory adapter that integrates LangChain with Azentiq Memory Manager.
    
    This class implements the LangChain BaseMemory interface and stores conversation
    history in Redis using the Azentiq Memory Manager.
    """
    # Define required public fields as Pydantic fields
    memory_key: str = Field(default="chat_history")
    input_key: str = Field(default="input")
    output_key: str = Field(default="output")
    return_messages: bool = Field(default=True)
    
    # Private attributes that don't need to be part of the schema
    _session_id: str = PrivateAttr()
    _memory_manager: MemoryManager = PrivateAttr()
    
    def __init__(
        self,
        session_id: str,
        redis_url: str = "redis://localhost:6379/0",
        memory_key: str = "chat_history",
        input_key: str = "input",
        output_key: str = "output",
        return_messages: bool = True,
        memory_manager: Optional[MemoryManager] = None,
    ):
        """Initialize the memory adapter.
        
        Args:
            session_id: Unique identifier for this conversation session
            redis_url: URL to Redis instance
            memory_key: Key to store memory under in LangChain
            input_key: Key for input value
            output_key: Key for output value
            return_messages: Whether to return messages or string
            memory_manager: Optional existing memory manager instance
        """
        # Initialize the base class with pydantic fields
        super().__init__(memory_key=memory_key, input_key=input_key, 
                        output_key=output_key, return_messages=return_messages)
        
        # Store the session ID as a private attribute
        self._session_id = session_id
        
        # Initialize the memory manager as a private attribute
        if memory_manager:
            self._memory_manager = memory_manager
        else:
            self._memory_manager = MemoryManager(redis_url=redis_url)
    
    @property
    def memory_variables(self) -> List[str]:
        """Return the memory variables needed by LangChain."""
        return [self.memory_key]
        
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables from Redis."""
        memories = []
        
        # Search for conversation memories in short-term tier
        query = {"session_id": self._session_id, "type": "conversation_turn"}
        logger.info(f"Loading conversation memory for session {self._session_id}")
        
        memories = self._memory_manager.search_by_metadata(
            query=query,
            tier=MemoryTier.SHORT_TERM
        )
        
        logger.info(f"Retrieved {len(memories)} conversation memories from Redis")
        
        # Sort by timestamp
        memories = sorted(
            memories, 
            key=lambda x: x.metadata.get("timestamp", ""),
            reverse=False  # Oldest first
        )
        
        # Process memories into messages
        if not self.return_messages:
            # If not returning messages, build a string of messages
            buffer = ""
            for memory in memories:
                buffer += f"{memory.metadata.get('role', 'unknown')}: {memory.content}\n"
            logger.info(f"Returning conversation history as string: {len(buffer)} chars")
            return {self.memory_key: buffer}
        else:
            # If returning messages, build a list of message objects
            messages = []
            for memory in memories:
                role = memory.metadata.get("role", "")
                if role == "user":
                    messages.append({"type": "human", "data": {"content": memory.content}})
                elif role == "assistant":
                    messages.append({"type": "ai", "data": {"content": memory.content}})
                elif role == "system":
                    messages.append({"type": "system", "data": {"content": memory.content}})
            logger.info(f"Returning conversation history as messages: {len(messages)} messages")
            return {self.memory_key: messages}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from this conversation turn to Redis.
        
        Args:
            inputs: Input values from the chain
            outputs: Output values from the chain
        """
        # Extract the input and output from the chain
        input_str = inputs[self.input_key]
        output_str = outputs[self.output_key]
        
        logger.info(f"Saving conversation context: User: '{input_str[:50]}...' AI: '{output_str[:50]}...'")

        # Get the highest turn number so far
        memories = self._memory_manager.search_by_metadata(
            query={"type": "conversation_turn", "session_id": self._session_id},
            tier=MemoryTier.SHORT_TERM
        )
        turn_count = len(memories)
        
        # Store the human message
        self._memory_manager.add_memory(
            content=input_str,
            metadata={
                "type": "conversation_turn",
                "role": "user",
                "turn": turn_count,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.7,
            tier=MemoryTier.SHORT_TERM,
            session_id=self._session_id
        )
        
        # Store the AI response
        ai_output = outputs[self.output_key]
        self._memory_manager.add_memory(
            content=ai_output,
            metadata={
                "type": "conversation_turn",
                "role": "assistant",
                "turn": turn_count + 1,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.7,
            tier=MemoryTier.SHORT_TERM,
            session_id=self._session_id
        )
    
    def clear(self) -> None:
        """Clear all memories for this session from Redis."""
        # Delete all conversation memories for this session
        memories = self._memory_manager.search_by_metadata(
            query={"type": "conversation_turn", "session_id": self._session_id},
            tier=MemoryTier.SHORT_TERM
        )
        
        # Delete each memory
        for memory in memories:
            self._memory_manager.delete(memory.memory_id)


class IoTMemoryManager:
    """IoT-specific memory manager for storing device telemetry, anomalies, and insights.
    
    This class handles storing and retrieving IoT data in Redis-backed tiered memory.
    """
    # This is a regular class, not a Pydantic model, so we use regular attributes
    
    def __init__(
        self,
        session_id: str,
        redis_url: str = "redis://localhost:6379/0",
        memory_manager: Optional[MemoryManager] = None,
    ):
        """Initialize the IoT Memory Manager.
        
        Args:
            session_id: Unique identifier for this session
            redis_url: URL to Redis instance
            memory_manager: Optional existing memory manager instance
        """
        # Store session ID as private attribute
        self._session_id = session_id
        self.session_id = session_id  # For backward compatibility
        
        # Initialize the memory manager
        if memory_manager:
            self._memory_manager = memory_manager
        else:
            self._memory_manager = MemoryManager(redis_url=redis_url)
            
        # For backward compatibility
        self.memory_manager = self._memory_manager
            
    def clear(self) -> None:
        """Clear all IoT-related memories for this session from Redis."""
        # Delete all memories for this session
        logger.info(f"Clearing all memories for session {self.session_id}")
        start_time = datetime.now()
        
        # Get existing memories for this session
        memories = self.memory_manager.search_by_metadata(
            query={"session_id": self.session_id},
        )
        
        # Delete each memory
        for memory in memories:
            self.memory_manager.delete_memory(
                memory_id=memory.memory_id,
                tier=MemoryTier.SHORT_TERM,
                session_id=self.session_id
            )
        
        logger.info(f"Cleared {len(memories)} memories in {(datetime.now() - start_time).total_seconds():.3f}s")
    
    def store_telemetry(self, device_id: str, metrics: Dict[str, float], importance: float = 0.6) -> str:
        """Store device telemetry in Redis short-term memory tier.
        
        Args:
            device_id: Identifier for the device
            metrics: Dictionary of metric readings
            importance: Importance score (0-1)
            
        Returns:
            memory_id: ID of the stored memory
        """
        logger.info(f"Storing telemetry for device {device_id}: {len(metrics)} metrics")
        return self._memory_manager.add_memory(
            content=str(metrics),  # Convert metrics to string
            metadata={
                "type": "telemetry",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": {k: str(v) for k, v in metrics.items()}  # Add metrics as searchable metadata
            },
            importance=importance,
            tier=MemoryTier.SHORT_TERM,
            session_id=self._session_id
        )
    
    def store_anomaly(self, device_id: str, anomaly_type: str, description: str, metrics: Dict[str, Any]) -> str:
        """Store anomaly detection in working memory for longer retention.
        
        Args:
            device_id: ID of the IoT device
            anomaly_type: Type of anomaly detected
            description: Description of the anomaly
            metrics: Metrics related to the anomaly
            
        Returns:
            memory_id: ID of the stored memory
        """
        return self.memory_manager.add_memory(
            content=description,
            metadata={
                "type": "anomaly",
                "device_id": device_id,
                "anomaly_type": anomaly_type,
                "timestamp": datetime.now().isoformat(),
                "metrics": {k: str(v) for k, v in metrics.items()}
            },
            importance=0.9,  # Anomalies are high importance
            tier=MemoryTier.WORKING,  # Store in working memory for longer retention
            session_id=self.session_id
        )
    
    def store_insight(self, device_id: str, insight_type: str, content: str) -> str:
        """Store AI-generated insights in working memory.
        
        Args:
            device_id: ID of the IoT device
            insight_type: Type of insight (trend, prediction, etc.)
            content: The insight content
            
        Returns:
            memory_id: ID of the stored memory
        """
        return self._memory_manager.add_memory(
            content=content,
            metadata={
                "type": "insight",
                "device_id": device_id,
                "insight_type": insight_type,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.8,
            tier=MemoryTier.WORKING,
            session_id=self._session_id
        )
    
    def get_device_history(self, device_id: str, memory_types: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent history for a specific device.
        
        Args:
            device_id: ID of the IoT device
            memory_types: List of memory types to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of memories related to this device
        """
        query = {"device_id": device_id}
        if memory_types:
            query["type"] = {"$in": memory_types}
        
        memories = self.memory_manager.search_by_metadata(
            query=query,
            limit=limit
        )
        
        return [
            {
                "content": m.content,
                "type": m.metadata.get("type", "unknown"),
                "timestamp": m.metadata.get("timestamp", ""),
                "importance": m.importance
            }
            for m in memories
        ]
    

        return self._memory_manager.add_memory(
            content=str(metrics),  # Convert metrics to string
            metadata={
                "type": "telemetry",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": {k: str(v) for k, v in metrics.items()}  # Add metrics as searchable metadata
            },
            importance=importance,
            tier=MemoryTier.SHORT_TERM,
            session_id=self._session_id
        )
    
    def store_anomaly(self, device_id: str, anomaly_type: str, metric_name: str, metric_value: Any, threshold: Any,
                  timestamp: datetime = None, importance: float = 0.8) -> str:
        """Store device anomaly in Redis working memory tier.
        
        Args:
            device_id: Identifier for the device
            anomaly_type: Type of anomaly detected
            metric_name: Name of the metric that triggered the anomaly
            metric_value: Value of the metric that triggered the anomaly
            threshold: Threshold value for the metric
            timestamp: Timestamp of the anomaly (optional)
            importance: Importance score (0-1)
            
        Returns:
            memory_id: ID of the stored memory
        """
        logger.info(f"Storing anomaly for device {device_id}: {anomaly_type} on {metric_name} = {metric_value} (threshold: {threshold})")
        return self._memory_manager.add_memory(
            content=f"Anomaly detected: {anomaly_type} on {metric_name} with value {metric_value} exceeding threshold {threshold}",
            metadata={
                "type": "anomaly",
                "device_id": device_id,
                "anomaly_type": anomaly_type,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "threshold": threshold,
                "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat()
            },
            importance=importance,
            tier=MemoryTier.WORKING,
            session_id=self._session_id
        )
    
    def store_insight(self, device_id: str, insight_type: str, content: str) -> str:
        """Store device insight in Redis working memory tier.
        
        Args:
            device_id: Identifier for the device
            insight_type: Type of insight generated
            content: Content of the insight
            
        Returns:
            memory_id: ID of the stored memory
        """
        logger.info(f"Storing {insight_type} insight for device {device_id}: {content[:100]}...")
        return self._memory_manager.add_memory(
            content=content,
            metadata={
                "type": "insight",
                "device_id": device_id,
                "insight_type": insight_type,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.8,
            tier=MemoryTier.WORKING,
            session_id=self._session_id
        )
    
    def get_device_history(self, device_id: str, memory_types: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get history of a specific device from Redis.
        
        Args:
            device_id: Identifier for the device
            memory_types: List of memory types to filter by
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memories related to this device
        """
        # Include session_id in the query to scope the search
        logger.info(f"Retrieving device history for device {device_id}, types={memory_types}, limit={limit}")
        start_time = datetime.now()
        
        memories = self._memory_manager.search_by_metadata(
            query={"device_id": device_id, "session_id": self._session_id},
            limit=limit
        )
        
        retrieval_time = (datetime.now() - start_time).total_seconds()
        memory_types_found = set([m.metadata.get("type", "unknown") for m in memories])
        logger.info(f"Retrieved {len(memories)} memories in {retrieval_time:.3f}s. Types: {memory_types_found}")
        
        # Convert to serializable format
        result = []
        for memory in memories:
            result.append({
                "id": memory.memory_id,
                "content": memory.content,
                "type": memory.metadata.get("type", "unknown"),
                "timestamp": memory.metadata.get("timestamp"),
                "importance": memory.importance,
                "tier": str(memory.tier)
            })
            
        return result

    def get_relevant_context(self, query_text: str) -> str:
        """Retrieve relevant context for a natural language query.
        
        This method retrieves memories from both SHORT_TERM and WORKING tiers
        that might be relevant to the query, and formats them into a context string.
        
        Args:
            query_text: The natural language query to find context for
            
        Returns:
            Formatted string containing relevant context
        """
        logger.info(f"Retrieving relevant context for query: {query_text}")
        start_time = datetime.now()
        
        # First get recent telemetry for all devices (from SHORT_TERM tier)
        recent_telemetry = self._memory_manager.search_by_metadata(
            query={"type": "telemetry", "session_id": self._session_id},
            tier=MemoryTier.SHORT_TERM,
            limit=20  # Limit to most recent readings
        )
        
        # Then get anomalies and insights (from WORKING tier)
        anomalies_and_insights = self._memory_manager.search_by_metadata(
            query={"session_id": self._session_id},
            tier=MemoryTier.WORKING,
            limit=10
        )
        
        # Filter anomalies and insights by type
        anomalies = [m for m in anomalies_and_insights if m.metadata.get("type") == "anomaly"]
        insights = [m for m in anomalies_and_insights if m.metadata.get("type") == "insight"]
        thresholds = [m for m in anomalies_and_insights if m.metadata.get("type") == "thresholds"]
        
        # Count by type for logging
        telemetry_count = len(recent_telemetry)
        anomaly_count = len(anomalies)
        insight_count = len(insights)
        threshold_count = len(thresholds)
        
        logger.info(f"Retrieved {telemetry_count} telemetry points, {anomaly_count} anomalies, "
                   f"{insight_count} insights, {threshold_count} threshold settings")
        
        # Format the context
        context_parts = []
        
        # First add insights as they are most important
        if insights:
            context_parts.append("INSIGHTS:")
            for insight in insights:
                device_id = insight.metadata.get("device_id", "unknown")
                timestamp = insight.metadata.get("timestamp", "unknown time")
                context_parts.append(f"Device {device_id} at {timestamp}: {insight.content}")
        
        # Then add anomalies
        if anomalies:
            context_parts.append("\nANOMALIES:")
            for anomaly in anomalies:
                device_id = anomaly.metadata.get("device_id", "unknown")
                timestamp = anomaly.metadata.get("timestamp", "unknown time")
                context_parts.append(f"Device {device_id} at {timestamp}: {anomaly.content}")
        
        # Group telemetry by device for better organization
        telemetry_by_device = {}
        for memory in recent_telemetry:
            device_id = memory.metadata.get("device_id")
            if device_id not in telemetry_by_device:
                telemetry_by_device[device_id] = []
            telemetry_by_device[device_id].append(memory)
        
        # Add recent telemetry for each device
        if telemetry_by_device:
            context_parts.append("\nRECENT TELEMETRY:")
            for device_id, memories in telemetry_by_device.items():
                # Sort by timestamp (most recent first)
                memories.sort(key=lambda x: x.metadata.get("timestamp", ""), reverse=True)
                # Take only the most recent 3 readings per device to keep context manageable
                for memory in memories[:3]:
                    timestamp = memory.metadata.get("timestamp", "unknown time")
                    try:
                        # Try to parse content as JSON for better formatting
                        metrics = json.loads(memory.content)
                        metrics_str = ", ".join(f"{k}: {v}" for k, v in metrics.items())
                        context_parts.append(f"Device {device_id} at {timestamp}: {metrics_str}")
                    except:
                        # Fallback if content is not JSON
                        context_parts.append(f"Device {device_id} at {timestamp}: {memory.content}")
        
        # Add threshold information
        if thresholds:
            context_parts.append("\nTHRESHOLDS:")
            for threshold in thresholds:
                device_id = threshold.metadata.get("device_id", "unknown")
                try:
                    threshold_data = json.loads(threshold.content.replace("'", "\"")) if isinstance(threshold.content, str) else threshold.content
                    threshold_str = ", ".join(f"{k}: {v}" for k, v in threshold_data.items())
                    context_parts.append(f"Device {device_id}: {threshold_str}")
                except:
                    context_parts.append(f"Device {device_id}: {threshold.content}")
        
        # Join all parts into a single context string
        context = "\n".join(context_parts)
        
        retrieval_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Context retrieval and formatting completed in {retrieval_time:.3f}s")
        logger.info(f"Final context length: {len(context)} chars")
        
        return context
