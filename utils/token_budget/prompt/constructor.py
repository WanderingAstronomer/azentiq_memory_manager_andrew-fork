"""Prompt construction with token budget awareness."""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from core.interfaces import Memory, MemoryTier
from utils.token_budget.estimator import TokenEstimator
from utils.token_budget.prompt.formatter import MemoryFormatter
from utils.budget_rules import BudgetRulesManager

logger = logging.getLogger(__name__)

class PromptConstructor:
    """Constructs prompts with memories while respecting token budgets."""
    
    def __init__(self, 
                token_estimator: TokenEstimator,
                formatter: Optional[MemoryFormatter] = None,
                budget_rules_manager: Optional[BudgetRulesManager] = None):
        """Initialize with token estimator and optional components.
        
        Args:
            token_estimator: TokenEstimator instance for token counting
            formatter: Optional MemoryFormatter instance (will create one if not provided)
            budget_rules_manager: Optional BudgetRulesManager for budget allocation
        """
        self.token_estimator = token_estimator
        self.formatter = formatter or MemoryFormatter()
        self.budget_rules_manager = budget_rules_manager
        self.current_component_id = None
        
    def set_context(self, component_id: Optional[str] = None):
        """Set the current component context.
        
        Args:
            component_id: Component identifier
        """
        self.current_component_id = component_id
        
    def allocate_token_budget(self, 
                             available_tokens: int,
                             memory_sections: Dict[str, List[Memory]]) -> Dict[str, int]:
        """Allocate token budget among memory sections.
        
        Args:
            available_tokens: Total tokens available for allocation
            memory_sections: Memory sections to allocate budget for
            
        Returns:
            Dictionary of section name to allocated token budget
        """
        # If no budget rules or component, allocate evenly
        if not self.budget_rules_manager or not self.current_component_id:
            # Equal distribution among sections
            section_count = len(memory_sections)
            if section_count == 0:
                return {}
            
            per_section = available_tokens // section_count
            return {section: per_section for section in memory_sections.keys()}
            
        # Use budget rules manager for allocation
        tier_allocations = self.budget_rules_manager.allocate_tier_budgets(
            self.current_component_id, available_tokens)
            
        # Map section names to tier allocations
        section_allocations = {}
        for section in memory_sections.keys():
            # Try to match section name to tier name
            if section.upper() in tier_allocations:
                section_allocations[section] = tier_allocations[section.upper()]
            else:
                # For sections like "relevance" that don't match a tier name,
                # allocate remaining budget evenly
                remaining_sections = set(memory_sections.keys()) - set(section_allocations.keys())
                if remaining_sections:
                    remaining_tokens = available_tokens - sum(section_allocations.values())
                    per_remaining = remaining_tokens // len(remaining_sections)
                    for remaining_section in remaining_sections:
                        section_allocations[remaining_section] = per_remaining
                        
        return section_allocations
        
    def construct_prompt(self,
                       user_input: str,
                       memory_sections: Dict[str, List[Memory]],
                       max_tokens: int,
                       system_message: Optional[str] = None,
                       format_templates: Optional[Dict[str, str]] = None,
                       memory_selectors: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, int]]:
        """Construct a prompt with selected memories within token budget.
        
        Args:
            user_input: User input text
            memory_sections: Dictionary of section name to memory list
            max_tokens: Maximum tokens for the entire prompt
            system_message: Optional system message to include
            format_templates: Optional dict of section name to format template
            memory_selectors: Optional dict of section name to memory selector
            
        Returns:
            Tuple of (formatted prompt, token usage stats)
        """
        # Initialize token tracking
        token_usage = {}
        
        # Calculate tokens for fixed content
        user_input_tokens = self.token_estimator.estimate_text(user_input)
        token_usage["user_input"] = user_input_tokens
        
        system_tokens = 0
        if system_message:
            system_tokens = self.token_estimator.estimate_text(system_message)
            token_usage["system"] = system_tokens
            
        # Calculate tokens available for memories
        fixed_tokens = user_input_tokens + system_tokens
        reserved_tokens = 50  # Reserved for formatting overhead
        available_memory_tokens = max(0, max_tokens - fixed_tokens - reserved_tokens)
        
        # Allocate token budget among memory sections
        section_allocations = self.allocate_token_budget(
            available_memory_tokens, memory_sections)
            
        # Track memory tokens by section
        token_usage["memories"] = {}
        
        # Format memory sections
        formatted_sections = {}
        
        for section_name, memories in memory_sections.items():
            # Skip if no allocation or no memories
            if not memories or section_name not in section_allocations:
                continue
                
            section_budget = section_allocations[section_name]
            
            # Use selector if provided
            selected_memories = memories
            if memory_selectors and section_name in memory_selectors:
                selector = memory_selectors[section_name]
                if callable(getattr(selector, "select_memories", None)):
                    selected_memories = selector.select_memories(memories, section_budget)
            
            # Get section template
            template = None
            if format_templates and section_name in format_templates:
                template = format_templates[section_name]
            
            # Format memories for this section
            section_content = self.formatter.format_memories(
                selected_memories,
                format_template=template,
                section_title=f"--- {section_name.upper()} MEMORIES ---"
            )
            
            # Skip if empty after formatting
            if not section_content:
                continue
                
            # Check if this section fits in budget
            section_tokens = self.token_estimator.estimate_text(section_content)
            if section_tokens <= section_budget:
                formatted_sections[section_name] = section_content
                token_usage["memories"][section_name] = section_tokens
        
        # Assemble final prompt
        prompt_parts = []
        
        # Add system message if provided
        if system_message:
            prompt_parts.append(system_message)
        
        # Add memory sections
        if formatted_sections:
            memory_content = "\n\n".join(formatted_sections.values())
            prompt_parts.append(memory_content)
        
        # Add user input
        prompt_parts.append(f"USER: {user_input}")
        
        # Join prompt parts
        prompt = "\n\n".join(prompt_parts)
        
        # Calculate total tokens
        token_usage["total"] = sum(token_usage.get("memories", {}).values()) + fixed_tokens
        
        return prompt, token_usage
