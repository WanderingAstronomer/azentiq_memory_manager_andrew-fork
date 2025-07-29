"""
Rule - Definition and implementation of memory progression rules
"""
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class Trigger:
    """Represents a rule trigger condition"""
    
    @staticmethod
    def from_config(config):
        """Create a trigger from configuration"""
        trigger_type = config.get('type')
        
        if trigger_type == 'event':
            return EventTrigger(config.get('event'))
        elif trigger_type == 'count':
            return CountTrigger(
                config.get('memory_type'),
                config.get('threshold'),
                config.get('tier')
            )
        elif trigger_type == 'schedule':
            return ScheduleTrigger(config.get('cron'))
        elif trigger_type == 'periodic':
            return PeriodicTrigger(config.get('interval'))
        else:
            raise ValueError(f"Unknown trigger type: {trigger_type}")


class EventTrigger(Trigger):
    """Trigger based on a specific event"""
    
    def __init__(self, event_name):
        self.event_name = event_name
        
    def matches(self, event_type):
        return event_type == self.event_name


class CountTrigger(Trigger):
    """Trigger based on count threshold"""
    
    def __init__(self, memory_type, threshold, tier=None):
        self.memory_type = memory_type
        self.threshold = threshold
        self.tier = tier
        
    def check(self, memory_manager):
        """Check if threshold has been reached"""
        query = {"type": self.memory_type}
        count = memory_manager.get_memory_count(self.tier, query)
        return count >= self.threshold


class ScheduleTrigger(Trigger):
    """Trigger based on cron schedule"""
    
    def __init__(self, cron_expression):
        self.cron_expression = cron_expression
        # Implementation would depend on scheduling library


class PeriodicTrigger(Trigger):
    """Trigger based on time interval"""
    
    def __init__(self, interval_seconds):
        self.interval = interval_seconds
        # Implementation would depend on scheduling library


class Action:
    """Represents an action to perform when a rule is triggered"""
    
    @staticmethod
    def from_config(config, memory_manager):
        """Create an action from configuration"""
        action_type = config.get('type')
        
        if action_type == 'create':
            return CreateAction(
                memory_manager,
                config.get('target_tier'),
                config.get('memory_type'),
                config.get('importance_calculator')
            )
        elif action_type == 'summarize':
            return SummarizeAction(
                memory_manager,
                config.get('source_tier'),
                config.get('target_tier'),
                config.get('source_type'),
                config.get('target_type'),
                config.get('summarizer')
            )
        elif action_type == 'promote':
            return PromoteAction(
                memory_manager,
                config.get('source_tier'),
                config.get('target_tier'),
                config.get('source_type'),
                config.get('target_type')
            )
        elif action_type == 'extract_and_store':
            return ExtractAndStoreAction(
                memory_manager,
                config.get('source_tier'),
                config.get('target_tier'),
                config.get('memory_type'),
                config.get('extractor')
            )
        else:
            raise ValueError(f"Unknown action type: {action_type}")


class CreateAction(Action):
    """Create a new memory"""
    
    def __init__(self, memory_manager, target_tier, memory_type, importance_calculator=None):
        self.memory_manager = memory_manager
        self.target_tier = target_tier
        self.memory_type = memory_type
        self.importance_calculator = importance_calculator
        
    def execute(self, memory=None, **context):
        """Execute the action"""
        # Implementation depends on specific use case


class SummarizeAction(Action):
    """Summarize memories into a new memory"""
    
    def __init__(self, memory_manager, source_tier, target_tier, source_type, target_type, summarizer=None):
        self.memory_manager = memory_manager
        self.source_tier = source_tier
        self.target_tier = target_tier
        self.source_type = source_type
        self.target_type = target_type
        self.summarizer = summarizer
        
    def execute(self, memory=None, **context):
        """Execute the action"""
        # Find memories to summarize
        memories = self.memory_manager.search_by_metadata(
            {"type": self.source_type},
            self.source_tier
        )
        
        if not memories:
            logger.info(f"No memories to summarize for type {self.source_type}")
            return
            
        # Generate summary (implementation depends on summarizer)
        summary = "Summary of memories"  # Placeholder
        
        # Store the summary
        self.memory_manager.add_memory(
            content=summary,
            tier=self.target_tier,
            metadata={"type": self.target_type},
            importance=0.8  # Summaries generally have high importance
        )
        
        logger.info(f"Created summary in {self.target_tier} tier")


class PromoteAction(Action):
    """Promote a memory from one tier to another"""
    
    def __init__(self, memory_manager, source_tier, target_tier, source_type=None, target_type=None):
        self.memory_manager = memory_manager
        self.source_tier = source_tier
        self.target_tier = target_tier
        self.source_type = source_type
        self.target_type = target_type
        
    def execute(self, memory, **context):
        """Execute the action"""
        if not memory:
            logger.warning("No memory provided for promotion")
            return
            
        # Create a copy in the target tier
        new_metadata = memory.metadata.copy()
        if self.target_type:
            new_metadata["type"] = self.target_type
            
        self.memory_manager.add_memory(
            content=memory.content,
            tier=self.target_tier,
            metadata=new_metadata,
            importance=memory.importance,
            session_id=memory.session_id
        )
        
        logger.info(f"Promoted memory from {self.source_tier} to {self.target_tier}")


class ExtractAndStoreAction(Action):
    """Extract information from a memory and store as a new memory"""
    
    def __init__(self, memory_manager, source_tier, target_tier, memory_type, extractor):
        self.memory_manager = memory_manager
        self.source_tier = source_tier
        self.target_tier = target_tier
        self.memory_type = memory_type
        self.extractor = extractor
        
    def execute(self, memory, **context):
        """Execute the action"""
        # Implementation depends on the extractor


class Rule:
    """A rule for memory progression"""
    
    def __init__(self, name, trigger, condition, action):
        self.name = name
        self.trigger = trigger
        self.condition = condition
        self.action = action
        
    @staticmethod
    def from_config(config, memory_manager):
        """Create a rule from configuration"""
        name = config.get('name', 'unnamed_rule')
        trigger_config = config.get('trigger', {})
        condition = config.get('condition', 'true')  # Default to always true
        action_config = config.get('action', {})
        
        trigger = Trigger.from_config(trigger_config)
        action = Action.from_config(action_config, memory_manager)
        
        return Rule(name, trigger, condition, action)
        
    def matches_event(self, event_type):
        """Check if rule matches an event type"""
        if hasattr(self.trigger, 'matches'):
            return self.trigger.matches(event_type)
        return False
        
    def evaluate_condition(self, memory=None, **context):
        """Evaluate the condition of this rule"""
        # For MVP, could use simple string conditions or just return True
        # More advanced implementation would parse and evaluate the condition
        return True
        
    def execute_action(self, memory=None, **context):
        """Execute the action of this rule"""
        try:
            logger.info(f"Executing rule '{self.name}'")
            self.action.execute(memory, **context)
            return True
        except Exception as e:
            logger.error(f"Error executing rule '{self.name}': {e}")
            return False
