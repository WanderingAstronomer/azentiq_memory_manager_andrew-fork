"""Token budget management for memory retrieval and prompt construction."""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime
import heapq
import logging

from core.interfaces import Memory, MemoryTier
from utils.budget_rules import BudgetRulesManager, AdaptationStrategy
from utils.token_budget.estimator import TokenEstimator
from utils.token_budget.selection import PriorityMemorySelector, RelevanceMemorySelector

logger = logging.getLogger(__name__)

class TokenBudgetManager:
    """Manages token budget for memories based on configuration rules."""
    
    def __init__(self, total_budget: int, config: Optional[Dict[str, Any]] = None,
                budget_rules_manager: Optional[BudgetRulesManager] = None):
        """Initialize with a total token budget and optional configuration.
        
        Args:
            total_budget: Total token budget
            config: Memory manager configuration
            budget_rules_manager: Optional pre-configured BudgetRulesManager
        """
        self.total_budget = total_budget
        self.used_tokens = 0
        self.memories: Dict[str, Tuple[Memory, int]] = {}
        
        # Set up budget rules manager
        self.config = config or {}
        self.budget_rules_manager = budget_rules_manager
        if config and not budget_rules_manager:
            self.budget_rules_manager = BudgetRulesManager(config)
        
        # Component and session tracking
        self.current_component_id = None
        self.current_session_id = None
        
        # Reserved tokens for system messages and overhead
        self.reserved_tokens = config.get('application', {}).get('reserved_tokens', 800) if config else 800
        
        # Initialize token estimator
        self.token_estimator = TokenEstimator(config)
        
        # Initialize memory selectors
        self.priority_selector = PriorityMemorySelector(self.token_estimator)
        self.relevance_selector = RelevanceMemorySelector(self.token_estimator)
    
    def set_context(self, component_id: Optional[str] = None, session_id: Optional[str] = None):
        """Set the current component and session context.
        
        Args:
            component_id: Current component ID
            session_id: Current session ID
        """
        if component_id:
            self.current_component_id = component_id
        if session_id:
            self.current_session_id = session_id
    
    def get_current_budget(self, tier: Optional[Union[MemoryTier, str]] = None) -> int:
        """Get the available budget for the current context.
        
        Args:
            tier: Optional memory tier to get budget for
            
        Returns:
            Available token budget
        """
        # Default to total budget if no rules manager
        if not self.budget_rules_manager or not self.current_component_id:
            return self.total_budget
            
        # Get component budget
        if tier is not None:
            # Get tier-specific budget
            return self.budget_rules_manager.get_tier_budget(self.current_component_id, tier)
        else:
            # Get total component budget
            return self.budget_rules_manager.get_component_budget(self.current_component_id)
    
    def track_memory(self, memory: Memory) -> int:
        """Track a memory and estimate its token usage.
        
        Args:
            memory: Memory to track
            
        Returns:
            Estimated token count for the memory
        """
        # Use the token estimator to get the token count
        token_count = self.token_estimator.estimate_memory(memory)
        
        self.memories[memory.memory_id] = (memory, token_count)
        self.used_tokens += token_count
        
        # Check if we need to apply adaptation strategies
        if self.budget_rules_manager and self.current_component_id:
            self._check_and_apply_adaptation()
        
        return token_count
    
    def untrack_memory(self, memory_id: str) -> int:
        """Stop tracking a memory.
        
        Args:
            memory_id: ID of memory to untrack
            
        Returns:
            Token count freed
        """
        if memory_id in self.memories:
            _, token_count = self.memories.pop(memory_id)
            self.used_tokens -= token_count
            return token_count
        return 0
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        
        Delegates to the TokenEstimator class.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return self.token_estimator.estimate_text(text)
    
    def estimate_memory_tokens(self, memory: Memory) -> int:
        """Estimate tokens for a memory object including content and metadata.
        
        Delegates to the TokenEstimator class.
        
        Args:
            memory: Memory object
            
        Returns:
            Estimated token count
        """
        return self.token_estimator.estimate_memory(memory)
        
    def get_available_budget(self, reserved_tokens: int = 0) -> int:
        """Get the available token budget after accounting for used tokens and reserved tokens.
        
        Args:
            reserved_tokens: Additional tokens to reserve (e.g., for system messages)
            
        Returns:
            Available token budget
        """
        total_reserved = self.reserved_tokens + reserved_tokens
        available = max(0, self.total_budget - self.used_tokens - total_reserved)
        return available
    
    def select_memories_by_priority(self, memories: List[Memory], 
                                   max_tokens: int, 
                                   recency_weight: float = 0.5,
                                   importance_weight: float = 0.5) -> List[Memory]:
        """Select memories based on a priority score of recency and importance.
        
        Delegates to PriorityMemorySelector.
        
        Args:
            memories: List of memory candidates
            max_tokens: Maximum tokens to allocate to selected memories
            recency_weight: Weight for recency in priority calculation (0.0-1.0)
            importance_weight: Weight for importance in priority calculation (0.0-1.0)
            
        Returns:
            Selected memories within token budget
        """
        # Get component-specific weights if available
        if self.budget_rules_manager and self.current_component_id:
            recency_weight, importance_weight = self.budget_rules_manager.get_priority_weights(
                self.current_component_id)
                
        return self.priority_selector.select_memories(
            memories, max_tokens, recency_weight=recency_weight, importance_weight=importance_weight)
    
    def select_short_term_memories(self, memories: List[Memory], max_tokens: int) -> List[Memory]:
        """Select short-term memories (conversational history).
        Prioritizes recent memories with higher weights for recency.
        
        Args:
            memories: Short-term memory candidates 
            max_tokens: Maximum tokens to use
            
        Returns:
            Selected memories
        """
        # For short-term, prioritize recency more
        return self.select_memories_by_priority(
            memories, max_tokens, recency_weight=0.8, importance_weight=0.2)
    
    def select_working_memories(self, memories: List[Memory], max_tokens: int) -> List[Memory]:
        """Select working memories (session context).
        Balances recency and importance.
        
        Args:
            memories: Working memory candidates
            max_tokens: Maximum tokens to use
            
        Returns:
            Selected memories
        """
        # For working memory, balance recency and importance
        return self.select_memories_by_priority(
            memories, max_tokens, recency_weight=0.5, importance_weight=0.5)
            
    def select_memories_by_relevance(self, memories: List[Memory], 
                                    query: str, 
                                    max_tokens: int,
                                    relevance_fn: Callable[[str, str], float] = None) -> List[Memory]:
        """Select memories based on relevance to a query.
        
        Delegates to RelevanceMemorySelector.
        
        Args:
            memories: Memory candidates
            query: User query to match against
            max_tokens: Maximum tokens to use
            relevance_fn: Optional function to calculate relevance score
            
        Returns:
            Selected relevant memories
        """
        # Get relevance threshold if available
        relevance_threshold = 0.1  # Default
        if self.budget_rules_manager and self.current_component_id:
            relevance_threshold = self.budget_rules_manager.get_relevance_threshold(
                self.current_component_id)
        
        # Use custom relevance function if provided
        if relevance_fn:
            # Create a one-time selector with custom function
            custom_selector = RelevanceMemorySelector(self.token_estimator, relevance_fn)
            return custom_selector.select_memories(
                memories, query, max_tokens, relevance_threshold)
        
        # Use our standard selector
        return self.relevance_selector.select_memories(
            memories, query, max_tokens, relevance_threshold)
            
    # The remaining methods will be refactored in subsequent phases
    # For now they should be kept as-is in token_budget.py
    # This ensures we maintain functionality while gradually refactoring
