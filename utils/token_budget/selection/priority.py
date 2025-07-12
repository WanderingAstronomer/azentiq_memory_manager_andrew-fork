"""Priority-based memory selection strategy."""

import heapq
from datetime import datetime
from typing import List, Tuple, Dict, Any

from core.interfaces import Memory
from utils.token_budget.estimator import TokenEstimator
from utils.token_budget.selection.base import MemorySelector

class PriorityMemorySelector(MemorySelector):
    """Selects memories based on priority score combining recency and importance.
    
    This selector uses a weighted combination of recency (time since last access)
    and importance scores to prioritize memories, then selects as many as possible
    within the token budget.
    """
    
    def select_memories(self, memories: List[Memory], max_tokens: int, 
                       recency_weight: float = 0.5,
                       importance_weight: float = 0.5) -> List[Memory]:
        """Select memories based on a priority score of recency and importance.
        
        Args:
            memories: List of memory candidates
            max_tokens: Maximum tokens to allocate to selected memories
            recency_weight: Weight for recency in priority calculation (0.0-1.0)
            importance_weight: Weight for importance in priority calculation (0.0-1.0)
            
        Returns:
            Selected memories within token budget
        """
        if not memories:
            return []
        
        # Calculate priority score for each memory
        now = datetime.utcnow()
        scored_memories = []
        
        for memory in memories:
            # Normalize recency (time since last access)
            time_diff = (now - memory.last_accessed_at).total_seconds() if memory.last_accessed_at else 0
            recency_score = 1.0 / (1.0 + time_diff / 3600)  # Higher score for more recent memories
            
            # Combine scores with weights
            priority = (recency_weight * recency_score + 
                       importance_weight * memory.importance)
            
            # Estimate token count
            token_count = self.token_estimator.estimate_memory(memory)
            
            # Store as tuple of (negative priority, token count, memory)
            # Use negative priority for min-heap to get highest priority first
            scored_memories.append((-priority, token_count, memory))
        
        # Sort by priority (using heapq for efficiency with large lists)
        heapq.heapify(scored_memories)
        
        # Select memories up to token budget
        selected = []
        total_tokens = 0
        
        while scored_memories and total_tokens < max_tokens:
            _, token_count, memory = heapq.heappop(scored_memories)
            
            # Skip if this memory would exceed budget
            if total_tokens + token_count > max_tokens:
                continue
                
            selected.append(memory)
            total_tokens += token_count
        
        return selected
