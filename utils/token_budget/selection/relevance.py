"""Relevance-based memory selection strategy."""

import re
import heapq
from typing import List, Tuple, Dict, Any, Callable, Optional

from core.interfaces import Memory
from utils.token_budget.estimator import TokenEstimator
from utils.token_budget.selection.base import MemorySelector

class RelevanceMemorySelector(MemorySelector):
    """Selects memories based on relevance to a query.
    
    This selector evaluates the relevance of memories to a user query,
    and selects the most relevant memories within a token budget. It supports
    pluggable relevance functions, defaulting to a simple keyword-based approach.
    """
    
    def __init__(self, token_estimator: TokenEstimator, relevance_fn: Optional[Callable[[str, str], float]] = None):
        """Initialize with token estimator and optional relevance function.
        
        Args:
            token_estimator: TokenEstimator instance for calculating token usage
            relevance_fn: Optional custom relevance function
        """
        super().__init__(token_estimator)
        self.relevance_fn = relevance_fn
    
    def select_memories(self, memories: List[Memory], query: str, 
                       max_tokens: int, relevance_threshold: float = 0.1) -> List[Memory]:
        """Select memories based on relevance to a query.
        
        Args:
            memories: Memory candidates
            query: User query to match against
            max_tokens: Maximum tokens to use
            relevance_threshold: Minimum relevance score (0.0-1.0)
            
        Returns:
            Selected relevant memories
        """
        if not memories:
            return []
            
        # Use provided relevance function or default
        relevance_fn = self.relevance_fn or self._default_relevance
        
        # Score memories by relevance
        scored_memories = []
        
        for memory in memories:
            # Calculate relevance score
            relevance = relevance_fn(query, memory.content)
            
            # Apply importance modifier
            combined_score = relevance * (1 + 0.5 * memory.importance)
            
            # Skip if below threshold
            if combined_score < relevance_threshold:
                continue
            
            # Get token count
            token_count = self.token_estimator.estimate_memory(memory)
            
            scored_memories.append((-combined_score, token_count, memory))
        
        # Sort by score
        heapq.heapify(scored_memories)
        
        # Select memories up to token budget
        selected = []
        total_tokens = 0
        
        while scored_memories and total_tokens < max_tokens:
            _, token_count, memory = heapq.heappop(scored_memories)
            
            # Skip if would exceed budget
            if total_tokens + token_count > max_tokens:
                continue
                
            selected.append(memory)
            total_tokens += token_count
        
        return selected
    
    def _default_relevance(self, query: str, text: str) -> float:
        """Calculate default relevance score using keyword matching.
        
        For production use, this should be replaced with semantic similarity
        using embeddings. The MVP can use this simple approach as a placeholder.
        
        Args:
            query: User query
            text: Memory content text
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Simple keyword matching
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not query_words or not text_words:
            return 0.0
            
        # Jaccard similarity
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        return intersection / union if union > 0 else 0.0
