"""
Progression Engine - Core logic for memory progression between tiers
"""
import logging
from typing import Dict, List, Optional, Any, Callable

from .rule import Rule
from .registry import TemplateRegistry

logger = logging.getLogger(__name__)

class ProgressionEngine:
    """
    Engine responsible for applying progression rules to memories.
    
    This class handles loading templates, processing events, and
    executing rules for memory progression between tiers.
    """
    
    def __init__(self, memory_manager, template_name=None, template_path=None):
        """
        Initialize the progression engine.
        
        Args:
            memory_manager: The memory manager instance
            template_name: Name of built-in template to use
            template_path: Path to custom template file
        """
        self.memory_manager = memory_manager
        self.registry = TemplateRegistry()
        self.rules = []
        self.active_template = None
        
        # Load template if provided
        if template_name:
            self.load_template_by_name(template_name)
        elif template_path:
            self.load_template_from_path(template_path)
    
    def load_template_by_name(self, name: str) -> bool:
        """
        Load a template by name from the registry.
        
        Args:
            name: Name of the template
            
        Returns:
            bool: True if template was loaded successfully
        """
        template = self.registry.get_template(name)
        if not template:
            logger.error(f"Template '{name}' not found")
            return False
            
        return self.apply_template(template)
    
    def load_template_from_path(self, path: str) -> bool:
        """
        Load a template from a file path.
        
        Args:
            path: Path to template file
            
        Returns:
            bool: True if template was loaded successfully
        """
        try:
            template = self.registry.load_from_path(path)
            return self.apply_template(template)
        except Exception as e:
            logger.error(f"Failed to load template from {path}: {e}")
            return False
    
    def apply_template(self, template: Dict) -> bool:
        """
        Apply a template configuration.
        
        Args:
            template: Template configuration dictionary
            
        Returns:
            bool: True if template was applied successfully
        """
        try:
            # Store active template
            self.active_template = template
            
            # Initialize rules from template
            self.rules = []
            for rule_config in template.get('rules', []):
                rule = Rule.from_config(rule_config, self.memory_manager)
                self.rules.append(rule)
                
            # Set up any schedulers or background tasks
            self._setup_schedulers()
            
            # Register event handlers
            self._register_event_handlers()
            
            logger.info(f"Applied template '{template.get('name')}' with {len(self.rules)} rules")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply template: {e}")
            return False
    
    def process_event(self, event_type: str, memory=None, **context):
        """
        Process an event and apply matching rules.
        
        Args:
            event_type: Type of event
            memory: Memory object related to event
            context: Additional context for the event
        """
        matching_rules = [r for r in self.rules if r.matches_event(event_type)]
        
        for rule in matching_rules:
            if rule.evaluate_condition(memory, **context):
                rule.execute_action(memory, **context)
    
    def _setup_schedulers(self):
        """Set up scheduled tasks for time-based rules"""
        # To be implemented based on scheduling library choice
        pass
        
    def _register_event_handlers(self):
        """Register event handlers with memory manager"""
        # Assuming memory_manager has an event bus or similar
        if hasattr(self.memory_manager, 'register_event_handler'):
            self.memory_manager.register_event_handler(
                'memory_added', self.process_event)
            self.memory_manager.register_event_handler(
                'memory_updated', self.process_event)
            # Add other events as needed
