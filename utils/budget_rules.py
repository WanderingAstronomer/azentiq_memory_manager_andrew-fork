"""
Token Budget Rules Implementation

This module provides classes and utilities for implementing token budget rules
according to the memory configuration schema.
"""

from enum import Enum, auto
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
import logging

from core.interfaces import Memory, MemoryTier

logger = logging.getLogger(__name__)


class AllocationStrategy(Enum):
    """Available strategies for token allocation."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    PRIORITY_BASED = "priority_based"
    ADAPTIVE = "adaptive"


class CompressionStrategy(Enum):
    """Available strategies for memory compression."""
    SUMMARIZE = "summarize"
    FILTER_BY_IMPORTANCE = "filter_by_importance"
    TRUNCATE = "truncate"
    HIERARCHICAL = "hierarchical"


class AdaptationStrategy(Enum):
    """Available strategies for adapting to token pressure."""
    REDUCE_MEMORIES = "reduce_memories"
    SUMMARIZE = "summarize"
    PRIORITIZE_WORKING = "prioritize_working" 
    PRIORITIZE_STM = "prioritize_stm"  # STM = Short-Term Memory


@dataclass
class ComponentTokenRules:
    """Component-specific token allocation rules."""
    max_memory_items: Optional[int] = None
    recency_weight: float = 0.5
    importance_weight: float = 0.5
    relevance_threshold: float = 0.2
    adaptation_strategy: AdaptationStrategy = AdaptationStrategy.REDUCE_MEMORIES
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentTokenRules':
        """Create ComponentTokenRules from dictionary."""
        adaptation_strategy = data.get('adaptation_strategy', 'reduce_memories')
        try:
            adaptation_strategy = AdaptationStrategy(adaptation_strategy)
        except ValueError:
            adaptation_strategy = AdaptationStrategy.REDUCE_MEMORIES
            
        return cls(
            max_memory_items=data.get('max_memory_items'),
            recency_weight=data.get('recency_weight', 0.5),
            importance_weight=data.get('importance_weight', 0.5),
            relevance_threshold=data.get('relevance_threshold', 0.2),
            adaptation_strategy=adaptation_strategy
        )


@dataclass
class MemoryCompressionSettings:
    """Settings for memory compression."""
    enabled: bool = False
    threshold: float = 0.9
    target_reduction: float = 0.3
    strategy: CompressionStrategy = CompressionStrategy.FILTER_BY_IMPORTANCE
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryCompressionSettings':
        """Create MemoryCompressionSettings from dictionary."""
        strategy = data.get('strategy', 'filter_by_importance')
        try:
            strategy = CompressionStrategy(strategy)
        except ValueError:
            strategy = CompressionStrategy.FILTER_BY_IMPORTANCE
            
        return cls(
            enabled=data.get('enabled', False),
            threshold=data.get('threshold', 0.9),
            target_reduction=data.get('target_reduction', 0.3),
            strategy=strategy
        )


@dataclass
class DynamicAllocationSettings:
    """Settings for dynamic token allocation."""
    active_boost: float = 1.5
    idle_reduction: float = 0.5
    minimum_allocation: float = 0.1
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DynamicAllocationSettings':
        """Create DynamicAllocationSettings from dictionary."""
        return cls(
            active_boost=data.get('active_boost', 1.5),
            idle_reduction=data.get('idle_reduction', 0.5),
            minimum_allocation=data.get('minimum_allocation', 0.1)
        )


@dataclass
class TokenMonitoringSettings:
    """Settings for token usage monitoring."""
    enabled: bool = True
    log_level: str = "info"
    alert_threshold: float = 0.95
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenMonitoringSettings':
        """Create TokenMonitoringSettings from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            log_level=data.get('log_level', 'info'),
            alert_threshold=data.get('alert_threshold', 0.95)
        )


class BudgetRulesManager:
    """Manager for token budget rules."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the BudgetRulesManager with configuration.
        
        Args:
            config: Dictionary containing token budget configuration
        """
        self.config = config
        self.global_token_limit = config.get('application', {}).get('global_token_limit', 8000)
        self.reserved_tokens = config.get('application', {}).get('reserved_tokens', 800)
        
        # Parse token budget section
        token_budget_config = config.get('token_budget', {})
        
        # Get allocation strategy
        strategy = token_budget_config.get('allocation_strategy', 'static')
        try:
            self.allocation_strategy = AllocationStrategy(strategy)
        except ValueError:
            logger.warning(f"Invalid allocation strategy '{strategy}', using static")
            self.allocation_strategy = AllocationStrategy.STATIC
        
        # Get default tier allocation
        self.default_tier_allocation = token_budget_config.get('default_tier_allocation', {
            'short_term': 0.6,
            'working': 0.3,
            'long_term': 0.1
        })
        
        # Parse component configuration
        self.component_configs = {}
        for component in config.get('components', []):
            component_id = component.get('id')
            if component_id:
                self.component_configs[component_id] = {
                    'token_limit': component.get('token_limit', 0),
                    'memory_allocation': component.get('memory_allocation', {}),
                    'memory_priority': component.get('memory_priority', 'medium'),
                    'token_rules': ComponentTokenRules.from_dict(
                        component.get('token_allocation_rules', {})
                    )
                }
        
        # Parse dynamic allocation settings
        self.dynamic_allocation = DynamicAllocationSettings.from_dict(
            token_budget_config.get('dynamic_allocation', {})
        )
        
        # Parse memory compression settings
        self.compression_settings = MemoryCompressionSettings.from_dict(
            token_budget_config.get('memory_compression', {})
        )
        
        # Parse token monitoring settings
        self.monitoring_settings = TokenMonitoringSettings.from_dict(
            token_budget_config.get('token_monitoring', {})
        )
        
        # Set up monitoring log level
        if self.monitoring_settings.enabled:
            numeric_level = getattr(logging, self.monitoring_settings.log_level.upper(), None)
            if isinstance(numeric_level, int):
                logger.setLevel(numeric_level)
    
    def get_component_budget(self, component_id: str) -> int:
        """
        Calculate the total token budget for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Token budget for the component
        """
        component_config = self.component_configs.get(component_id)
        if not component_config:
            return 0
            
        return component_config.get('token_limit', 0)
    
    def get_tier_budget(self, component_id: str, tier: Union[MemoryTier, str]) -> int:
        """
        Calculate the token budget for a specific memory tier in a component.
        
        Args:
            component_id: ID of the component
            tier: Memory tier (SHORT_TERM, WORKING, LONG_TERM)
            
        Returns:
            Token budget for the specified tier in the component
        """
        component_config = self.component_configs.get(component_id)
        if not component_config:
            return 0
        
        component_budget = component_config.get('token_limit', 0)
        
        # Get tier name as string
        tier_name = tier.value if isinstance(tier, MemoryTier) else tier
        
        # Get component-specific tier allocation or default
        memory_allocation = component_config.get('memory_allocation', {})
        tier_allocation = memory_allocation.get(tier_name)
        
        if tier_allocation is None:
            # Fall back to default allocation
            tier_allocation = self.default_tier_allocation.get(tier_name, 0.3)
        
        # Apply dynamic allocation if needed
        if self.allocation_strategy == AllocationStrategy.DYNAMIC:
            # This would need activity data to fully implement
            # For now, use default allocation
            pass
        
        return int(component_budget * tier_allocation)
    
    def adjust_budget_by_activity(self, component_id: str, is_active: bool) -> float:
        """
        Adjust the token budget multiplier based on component activity.
        
        Args:
            component_id: ID of the component
            is_active: Whether the component is currently active
            
        Returns:
            Multiplier to apply to the component's token budget
        """
        if self.allocation_strategy != AllocationStrategy.DYNAMIC:
            return 1.0
        
        if is_active:
            return self.dynamic_allocation.active_boost
        else:
            # Don't go below minimum allocation
            return max(self.dynamic_allocation.idle_reduction, 
                      self.dynamic_allocation.minimum_allocation)
    
    def should_compress_memories(self, usage_ratio: float) -> bool:
        """
        Check if memory compression should be triggered.
        
        Args:
            usage_ratio: Current token usage ratio (0.0-1.0)
            
        Returns:
            Whether compression should be triggered
        """
        if not self.compression_settings.enabled:
            return False
        
        return usage_ratio >= self.compression_settings.threshold
    
    def get_compression_target(self, current_tokens: int) -> int:
        """
        Calculate the target token count after compression.
        
        Args:
            current_tokens: Current token count
            
        Returns:
            Target token count after compression
        """
        if not self.compression_settings.enabled:
            return current_tokens
        
        return int(current_tokens * (1 - self.compression_settings.target_reduction))
    
    def get_component_rules(self, component_id: str) -> Optional[ComponentTokenRules]:
        """
        Get token allocation rules for a specific component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Component token rules or None if component not found
        """
        component_config = self.component_configs.get(component_id)
        if not component_config:
            return None
        
        return component_config.get('token_rules')
    
    def get_priority_multiplier(self, component_id: str) -> float:
        """
        Get priority multiplier for a component based on memory_priority.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Priority multiplier (higher for higher priority)
        """
        component_config = self.component_configs.get(component_id)
        if not component_config:
            return 1.0
        
        priority = component_config.get('memory_priority', 'medium')
        
        # Priority multipliers
        if priority == 'high':
            return 1.5
        elif priority == 'low':
            return 0.7
        else:  # medium
            return 1.0
    
    def log_token_usage(self, component_id: str, tier: Union[MemoryTier, str], 
                        used: int, allocated: int) -> None:
        """
        Log token usage information.
        
        Args:
            component_id: ID of the component
            tier: Memory tier
            used: Tokens used
            allocated: Tokens allocated
        """
        if not self.monitoring_settings.enabled:
            return
        
        usage_ratio = used / max(allocated, 1)
        tier_name = tier.value if isinstance(tier, MemoryTier) else tier
        
        log_message = (f"Token usage for component '{component_id}', tier '{tier_name}': "
                       f"{used}/{allocated} ({usage_ratio:.1%})")
        
        if usage_ratio >= self.monitoring_settings.alert_threshold:
            logger.warning(f"⚠️ {log_message} - Approaching limit!")
        else:
            logger.info(log_message)
    
    def get_adaptive_action(self, component_id: str, 
                           usage_ratio: float) -> Optional[AdaptationStrategy]:
        """
        Get the appropriate adaptation action for a component based on token pressure.
        
        Args:
            component_id: ID of the component
            usage_ratio: Current token usage ratio
            
        Returns:
            Adaptation strategy to apply or None if no adaptation needed
        """
        if usage_ratio < self.compression_settings.threshold:
            return None
            
        component_rules = self.get_component_rules(component_id)
        if not component_rules:
            return AdaptationStrategy.REDUCE_MEMORIES
            
        return component_rules.adaptation_strategy
