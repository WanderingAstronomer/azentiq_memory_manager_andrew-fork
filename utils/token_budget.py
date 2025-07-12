"""Token budget management utilities for memory retrieval and prompt construction."""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime
import re
import heapq
import logging

from core.interfaces import Memory, MemoryTier
from utils.budget_rules import BudgetRulesManager, AdaptationStrategy as AdaptationStrategyEnum
from utils.token_budget.estimator import TokenEstimator
from utils.token_budget.selection import PriorityMemorySelector, RelevanceMemorySelector
from utils.token_budget.adaptation import (
    AdaptationStrategy,
    ReduceAdaptationStrategy,
    SummarizeAdaptationStrategy,
    PrioritizeTierStrategy
)
from utils.token_budget.prompt import MemoryFormatter, PromptConstructor

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
        
        # Initialize adaptation strategies
        self.adaptation_strategies = {
            AdaptationStrategyEnum.REDUCE: ReduceAdaptationStrategy(self.token_estimator),
            AdaptationStrategyEnum.SUMMARIZE: SummarizeAdaptationStrategy(self.token_estimator),
            AdaptationStrategyEnum.PRIORITIZE: PrioritizeTierStrategy(self.token_estimator)
        }
        
        # Initialize memory formatter and prompt constructor
        self.memory_formatter = MemoryFormatter()
        self.prompt_constructor = PromptConstructor(
            self.token_estimator,
            formatter=self.memory_formatter,
            budget_rules_manager=self.budget_rules_manager
        )
    
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
            
        # Update prompt constructor context
        self.prompt_constructor.set_context(component_id)
    
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
        token_count = self.estimate_memory_tokens(memory)
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
        return max(0, self.total_budget - self.used_tokens - reserved_tokens - self.reserved_tokens)
    
    def format_memories_for_prompt(self, memories: List[Memory], format_template: str = None) -> str:
        """Format a list of memories for inclusion in a prompt.
        
        Delegates to the MemoryFormatter class.
        
        Args:
            memories: List of Memory objects to format
            format_template: Optional template string with {placeholder} format
            
        Returns:
            Formatted memory string for prompt inclusion
        """
        return self.memory_formatter.format_memories(memories, format_template=format_template)
    
    def allocate_tier_budgets(self, available_tokens: int) -> Dict[str, int]:
        """Allocate available tokens among memory tiers.
        
        Args:
            available_tokens: Total available tokens
            
        Returns:
            Dictionary of tier to allocated token budget
        """
        # Default allocation if no rules manager
        if not self.budget_rules_manager or not self.current_component_id:
            # Equal distribution among tiers
            tiers = [t.name for t in MemoryTier]
            per_tier = available_tokens // len(tiers)
            return {tier: per_tier for tier in tiers}
            
        # Get tier allocations from rules manager
        return self.budget_rules_manager.allocate_tier_budgets(
            self.current_component_id, available_tokens)
    
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
        if not memories:
            return []
            
        # Get component-specific weights if available
        if self.budget_rules_manager and self.current_component_id:
            component_weights = self.budget_rules_manager.get_priority_weights(
                self.current_component_id)
            if component_weights:
                recency_weight, importance_weight = component_weights
                
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
        if not memories:
            return []
            
        # Get relevance threshold if available
        relevance_threshold = 0.1  # Default
        if self.budget_rules_manager and self.current_component_id:
            threshold = self.budget_rules_manager.get_relevance_threshold(
                self.current_component_id)
            if threshold is not None:
                relevance_threshold = threshold
        
        # Use custom relevance function if provided
        if relevance_fn:
            # Create a one-time selector with custom function
            custom_selector = RelevanceMemorySelector(self.token_estimator, relevance_fn)
            return custom_selector.select_memories(
                memories, query, max_tokens, relevance_threshold)
        
        # Use our standard selector
        return self.relevance_selector.select_memories(
            memories, query, max_tokens, relevance_threshold)
    
    def _check_and_apply_adaptation(self) -> bool:
        """Check if we need to adapt to token pressure and apply strategies.
        
        Returns:
            True if adaptation was applied, False otherwise
        """
        if not self.budget_rules_manager or not self.current_component_id:
            return False
            
        # Check if we're over budget
        component_budget = self.budget_rules_manager.get_component_budget(
            self.current_component_id)
        
        # No need to adapt if under budget
        if self.used_tokens <= component_budget:
            return False
            
        # Get adaptation strategy
        strategy_type = self.budget_rules_manager.get_adaptation_strategy(
            self.current_component_id)
        
        # Get appropriate strategy object
        strategy_obj = self.adaptation_strategies.get(
            strategy_type, self.adaptation_strategies[AdaptationStrategyEnum.REDUCE])
        
        # Initialize kwargs for the strategy
        strategy_kwargs = {}
        
        # Add strategy-specific parameters
        if strategy_type == AdaptationStrategyEnum.REDUCE:
            # Get reduction target (default: reduce by 20%)
            reduction_target = 0.2  # Default
            if self.budget_rules_manager:
                reduction_target = self.budget_rules_manager.get_reduction_target()
            strategy_kwargs['reduction_target'] = reduction_target
            
        elif strategy_type == AdaptationStrategyEnum.PRIORITIZE:
            # Get priority tier
            priority_tier = self.budget_rules_manager.get_priority_tier(
                self.current_component_id)
            strategy_kwargs['priority_tier'] = priority_tier
            
        # Apply the strategy
        updated_memories, new_used_tokens, removed_ids = strategy_obj.adapt_memories(
            self.memories, self.used_tokens, component_budget, **strategy_kwargs)
        
        # Update manager state with strategy results
        self.memories = updated_memories
        self.used_tokens = new_used_tokens
        
        return len(removed_ids) > 0
    
    def construct_prompt_with_memories(self, 
                                      user_input: str, 
                                      memories: Dict[str, List[Memory]],
                                      max_tokens: int,
                                      system_message: Optional[str] = None,
                                      format_templates: Dict[str, str] = None) -> Tuple[str, Dict[str, int]]:
        """Construct a prompt with selected memories within token budget.
        
        Delegates to the PromptConstructor class with pre-selection of memories.
        
        Args:
            user_input: User input text
            memories: Dictionary of memory type to memory list
            max_tokens: Maximum tokens for the entire prompt
            system_message: Optional system message to include
            format_templates: Optional dict of memory type to format template
            
        Returns:
            Tuple of (formatted prompt, token usage stats)
        """
        # Prepare memory selectors for the constructor
        memory_selectors = {}
        
        # Create memory sections with selected memories
        memory_sections = {}
        
        # Calculate tokens for fixed content
        user_input_tokens = self.estimate_tokens(user_input)
        system_tokens = 0
        if system_message:
            system_tokens = self.estimate_tokens(system_message)
            
        # Calculate tokens available for memories
        fixed_tokens = user_input_tokens + system_tokens
        reserved_tokens = 50  # Reserved for formatting overhead
        available_memory_tokens = max(0, max_tokens - fixed_tokens - reserved_tokens)
        
        # Allocate tokens by memory type
        memory_type_allocation = self.allocate_tier_budgets(available_memory_tokens)
        
        # Select memories by type
        for memory_type, memory_list in memories.items():
            # Skip if no allocation for this type
            if memory_type not in memory_type_allocation or not memory_list:
                continue
                
            # Get allocation
            type_tokens = memory_type_allocation[memory_type]
            
            # Select memories within budget
            if memory_type == "relevance":
                # Use relevance selection if we have user input
                selected = self.select_memories_by_relevance(
                    memory_list, user_input, type_tokens)
                memory_selectors[memory_type] = self.relevance_selector
            else:
                # Otherwise use priority selection
                selected = self.select_memories_by_priority(
                    memory_list, type_tokens)
                memory_selectors[memory_type] = self.priority_selector
                
            # Add to sections if we have selected memories
            if selected:
                memory_sections[memory_type] = selected
        
        # Delegate to prompt constructor
        return self.prompt_constructor.construct_prompt(
            user_input=user_input,
            memory_sections=memory_sections,
            max_tokens=max_tokens,
            system_message=system_message,
            format_templates=format_templates,
            memory_selectors=memory_selectors
        )
