"""Prioritize tier adaptation strategy implementation."""

import logging
from typing import Dict, List, Any, Tuple, Optional

from core.interfaces import Memory, MemoryTier
from utils.token_budget.adaptation.base import AdaptationStrategy

logger = logging.getLogger(__name__)

class PrioritizeTierStrategy(AdaptationStrategy):
    """Strategy to prioritize a specific memory tier by reducing others.
    
    This strategy preserves memories in a priority tier while reducing 
    memories in other tiers to meet the token budget.
    """
    
    def adapt_memories(self, 
                     memories: Dict[str, Tuple[Memory, int]], 
                     used_tokens: int,
                     target_tokens: int,
                     priority_tier: MemoryTier = None,
                     **kwargs) -> Tuple[Dict[str, Tuple[Memory, int]], int, List[str]]:
        """Apply prioritize tier strategy to memories.
        
        Args:
            memories: Dictionary of memory_id -> (Memory, token_count)
            used_tokens: Current token usage
            target_tokens: Target token usage to reduce to
            priority_tier: The tier to prioritize (preserve)
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (updated_memories, new_used_tokens, removed_memory_ids)
        """
        if not priority_tier or used_tokens <= target_tokens:
            # No priority tier specified or already under target
            return memories, used_tokens, []
            
        # Calculate tokens to free
        tokens_to_free = used_tokens - target_tokens
        
        # Group memories by tier
        tier_memories = {}
        for memory_id, (memory, token_count) in memories.items():
            tier = memory.tier
            if tier not in tier_memories:
                tier_memories[tier] = []
            tier_memories[tier].append((memory_id, token_count))
        
        # Don't remove from priority tier
        tiers_to_reduce = [t for t in tier_memories.keys() if t != priority_tier]
        
        # No other tiers to reduce
        if not tiers_to_reduce:
            logger.info(f"Cannot prioritize {priority_tier} tier - no other tiers to reduce")
            return memories, used_tokens, []
        
        # Start removing from non-priority tiers
        freed_tokens = 0
        removed_ids = []
        
        for tier in tiers_to_reduce:
            # Skip if we've freed enough
            if freed_tokens >= tokens_to_free:
                break
                
            for memory_id, token_count in tier_memories[tier]:
                removed_ids.append(memory_id)
                freed_tokens += token_count
                
                if freed_tokens >= tokens_to_free:
                    break
        
        # Update memories and token count
        updated_memories = {k: v for k, v in memories.items() if k not in removed_ids}
        new_used_tokens = used_tokens - freed_tokens
        
        logger.info(f"Prioritized {priority_tier} tier by removing {len(removed_ids)} memories from other tiers")
        return updated_memories, new_used_tokens, removed_ids
