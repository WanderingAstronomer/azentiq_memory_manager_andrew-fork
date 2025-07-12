"""Base adaptation strategy interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional

from core.interfaces import Memory, MemoryTier
from utils.token_budget.estimator import TokenEstimator

class AdaptationStrategy(ABC):
    """Abstract base class for memory adaptation strategies.
    
    Adaptation strategies are responsible for adjusting memory usage
    when token budgets are exceeded, through techniques like reducing,
    summarizing, or prioritizing memories.
    """
    
    def __init__(self, token_estimator: TokenEstimator):
        """Initialize with token estimator.
        
        Args:
            token_estimator: TokenEstimator instance for calculating token usage
        """
        self.token_estimator = token_estimator
    
    @abstractmethod
    def adapt_memories(self, 
                     memories: Dict[str, Tuple[Memory, int]], 
                     used_tokens: int,
                     target_tokens: int,
                     **kwargs) -> Tuple[Dict[str, Tuple[Memory, int]], int, List[str]]:
        """Apply adaptation strategy to memories to reduce token usage.
        
        Args:
            memories: Dictionary of memory_id -> (Memory, token_count)
            used_tokens: Current token usage
            target_tokens: Target token usage to reduce to
            **kwargs: Strategy-specific parameters
            
        Returns:
            Tuple of (updated_memories, new_used_tokens, removed_memory_ids)
        """
        pass
