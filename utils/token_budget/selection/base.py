"""Base memory selector interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from core.interfaces import Memory
from utils.token_budget.estimator import TokenEstimator

class MemorySelector(ABC):
    """Abstract base class for memory selection strategies.
    
    Memory selectors are responsible for selecting memories within a token budget
    based on various criteria such as priority, relevance, or other metrics.
    """
    
    def __init__(self, token_estimator: TokenEstimator):
        """Initialize with token estimator.
        
        Args:
            token_estimator: TokenEstimator instance for calculating token usage
        """
        self.token_estimator = token_estimator
    
    @abstractmethod
    def select_memories(self, memories: List[Memory], max_tokens: int, **kwargs) -> List[Memory]:
        """Select memories within the token budget.
        
        Args:
            memories: List of candidate memories
            max_tokens: Maximum tokens to allocate
            **kwargs: Implementation-specific parameters
            
        Returns:
            Selected memories within token budget
        """
        pass
