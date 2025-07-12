"""
LangChain Memory Adapter for Azentiq Memory Manager.

This module provides a custom memory implementation that integrates 
LangChain with Azentiq Memory Manager.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage

from core.interfaces import MemoryTier
from memory_manager import MemoryManager


class AzentiqMemory(BaseChatMemory):
    """LangChain Memory implementation using Azentiq Memory Manager."""
    
    memory_key: str = "chat_history"
    
    def __init__(
        self,
        session_id: str,
        redis_url: str = "redis://localhost:6379/0",
        max_token_limit: int = 4000,
        return_messages: bool = True,
        memory_manager: Optional[MemoryManager] = None
    ):
        """Initialize with Azentiq Memory Manager.
        
        Args:
            session_id: Unique identifier for this conversation
            redis_url: URL to Redis instance
            max_token_limit: Maximum number of tokens to include
            return_messages: Whether to return messages or string
            memory_manager: Optional existing memory manager instance
        """
        super().__init__(return_messages=return_messages, input_key="input", output_key="output")
        self.session_id = session_id
        self.max_token_limit = max_token_limit
        
        # Use provided memory manager or create a new one
        if memory_manager:
            self.memory_manager = memory_manager
        else:
            self.memory_manager = MemoryManager(redis_url=redis_url)
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables from Azentiq Memory Manager."""
        # Get conversation history
        messages = self.chat_memory.messages
        
        # If returning messages directly
        if self.return_messages:
            return {self.memory_key: messages}
        
        # Convert messages to string
        return {self.memory_key: self._messages_to_string(messages)}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from this conversation turn to memory."""
        # Save to internal chat memory (standard LangChain behavior)
        super().save_context(inputs, outputs)
        
        # Extract input/output
        input_text = inputs.get(self.input_key, "")
        output_text = outputs.get(self.output_key, "")
        
        # Get current message count for turn numbering
        current_memories = self.memory_manager.search_by_metadata(
            query={"role": {"$exists": True}},
            tier=MemoryTier.SHORT_TERM,
            session_id=self.session_id
        )
        turn_count = len(current_memories)
        
        # Save user message to short-term memory
        if input_text:
            self.memory_manager.add_memory(
                content=input_text,
                metadata={
                    "role": "user",
                    "turn": turn_count,
                    "type": "conversation_turn",
                    "timestamp": datetime.now().isoformat()
                },
                importance=1.0,
                tier=MemoryTier.SHORT_TERM,
                session_id=self.session_id
            )
        
        # Save assistant response to short-term memory
        if output_text:
            self.memory_manager.add_memory(
                content=output_text,
                metadata={
                    "role": "assistant", 
                    "turn": turn_count + 1,
                    "type": "conversation_turn",
                    "timestamp": datetime.now().isoformat()
                },
                importance=1.0,
                tier=MemoryTier.SHORT_TERM,
                session_id=self.session_id
            )
    
    def store_telemetry(self, device_id: str, metrics: Dict[str, Any], importance: float = 0.6) -> str:
        """Store device telemetry in the appropriate memory tier.
        
        Args:
            device_id: ID of the IoT device
            metrics: Dictionary of metric readings
            importance: Importance score (0-1)
            
        Returns:
            memory_id: ID of the stored memory
        """
        return self.memory_manager.add_memory(
            content=str(metrics),  # Convert metrics to string
            metadata={
                "type": "telemetry",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": {k: str(v) for k, v in metrics.items()}  # Add metrics as searchable metadata
            },
            importance=importance,
            tier=MemoryTier.SHORT_TERM,
            session_id=self.session_id
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
        return self.memory_manager.add_memory(
            content=content,
            metadata={
                "type": "insight",
                "device_id": device_id,
                "insight_type": insight_type,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.8,
            tier=MemoryTier.WORKING,
            session_id=self.session_id
        )
    
    def get_device_history(self, device_id: str, limit: int = 10) -> List[Dict]:
        """Get recent history for a specific device.
        
        Args:
            device_id: ID of the IoT device
            limit: Maximum number of records to return
            
        Returns:
            List of memories related to this device
        """
        memories = self.memory_manager.search_by_metadata(
            query={"device_id": device_id},
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
    
    def clear(self) -> None:
        """Clear all memories for this session."""
        # Get all memories for this session
        short_term_memories = self.memory_manager.search_by_metadata(
            query={"session_id": self.session_id},
            tier=MemoryTier.SHORT_TERM
        )
        
        # Delete each memory
        for memory in short_term_memories:
            self.memory_manager.delete_memory(
                memory_id=memory.memory_id,
                tier=MemoryTier.SHORT_TERM,
                session_id=self.session_id
            )
