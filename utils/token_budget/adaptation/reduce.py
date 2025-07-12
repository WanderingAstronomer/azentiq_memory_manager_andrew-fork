"""Reduce adaptation strategy implementation."""

from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

from core.interfaces import Memory
from utils.token_budget.adaptation.base import AdaptationStrategy

class ReduceAdaptationStrategy(AdaptationStrategy):
    """Strategy to reduce token usage by removing least important memories.
    
    This strategy sorts memories by a priority score combining recency and importance,
    then removes the lowest priority memories until the target token usage is met.
    """
    
    def adapt_memories(self, 
                     memories: Dict[str, Tuple[Memory, int]], 
                     used_tokens: int,
                     target_tokens: int,
                     reduction_target: float = 0.2,
                     **kwargs) -> Tuple[Dict[str, Tuple[Memory, int]], int, List[str]]:
        """Apply reduction strategy to memories.
        
        Args:
            memories: Dictionary of memory_id -> (Memory, token_count)
            used_tokens: Current token usage
            target_tokens: Target token usage to reduce to
            reduction_target: Fraction of tokens to attempt to free (0.0-1.0)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Tuple of (updated_memories, new_used_tokens, removed_memory_ids)
        """
        if used_tokens <= target_tokens:
            # Already under target, no adaptation needed
            return memories, used_tokens, []
            
        # Calculate tokens to free
        tokens_to_free = max(
            int(used_tokens * reduction_target),  # Default percentage-based reduction
            used_tokens - target_tokens  # Minimum needed to meet target
        )
        
        # Score memories by priority (combine recency and importance)
        now = datetime.utcnow()
        scored_memories = []
        
        for memory_id, (memory, token_count) in memories.items():
            # Calculate recency score
            time_diff = (now - memory.last_accessed_at).total_seconds() if memory.last_accessed_at else 0
            recency_score = 1.0 / (1.0 + time_diff / 3600)
            
            # Combined score (lower is less important to keep)
            priority = recency_score + memory.importance
            scored_memories.append((priority, memory_id, token_count))
        
        # Sort by priority (ascending, so we remove lowest priority first)
        scored_memories.sort()
        
        # Remove memories until we've freed enough tokens
        freed_tokens = 0
        removed_ids = []
        
        for _, memory_id, token_count in scored_memories:
            if freed_tokens >= tokens_to_free:
                break
                
            # Remove this memory
            removed_ids.append(memory_id)
            freed_tokens += token_count
        
        # Update memories and token count
        updated_memories = {k: v for k, v in memories.items() if k not in removed_ids}
        new_used_tokens = used_tokens - freed_tokens
        
        return updated_memories, new_used_tokens, removed_ids
