"""
Template Registry - Manages memory progression templates
"""
import os
import logging
import yaml
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class TemplateRegistry:
    """
    Registry for memory progression templates.
    
    Handles loading, validation, and retrieval of templates.
    """
    
    def __init__(self):
        """Initialize the template registry"""
        self._templates = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load all built-in templates"""
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        if not os.path.exists(template_dir):
            logger.warning(f"Templates directory not found: {template_dir}")
            return
            
        for filename in os.listdir(template_dir):
            if filename.endswith(".yaml"):
                name = os.path.splitext(filename)[0]
                path = os.path.join(template_dir, filename)
                try:
                    self._templates[name] = self.load_from_path(path)
                    logger.info(f"Loaded template '{name}' from {path}")
                except Exception as e:
                    logger.error(f"Failed to load template {path}: {e}")
    
    def get_template(self, name: str) -> Optional[Dict]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template configuration or None if not found
        """
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """
        List all available templates.
        
        Returns:
            List of template names
        """
        return list(self._templates.keys())
    
    def register_template(self, name: str, config: Dict):
        """
        Register a new template.
        
        Args:
            name: Template name
            config: Template configuration
        """
        if name in self._templates:
            logger.warning(f"Overwriting existing template '{name}'")
            
        self._templates[name] = config
        logger.info(f"Registered template '{name}'")
    
    def load_from_path(self, path: str) -> Dict:
        """
        Load a template from a file.
        
        Args:
            path: Path to template file
            
        Returns:
            Template configuration
            
        Raises:
            FileNotFoundError: If template file not found
            ValueError: If template is invalid
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template file not found: {path}")
            
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            
        self._validate_template(config)
        return config
    
    def _validate_template(self, config: Dict):
        """
        Validate template configuration.
        
        Args:
            config: Template configuration
            
        Raises:
            ValueError: If template is invalid
        """
        # Check required fields
        if 'name' not in config:
            raise ValueError("Template must have a name")
            
        if 'tiers' not in config:
            raise ValueError("Template must define tiers")
            
        if 'rules' not in config:
            raise ValueError("Template must define rules")
            
        # Validate rules (basic validation)
        for rule in config['rules']:
            if 'name' not in rule:
                raise ValueError("Each rule must have a name")
                
            if 'trigger' not in rule:
                raise ValueError(f"Rule '{rule['name']}' must have a trigger")
                
            if 'action' not in rule:
                raise ValueError(f"Rule '{rule['name']}' must have an action")
