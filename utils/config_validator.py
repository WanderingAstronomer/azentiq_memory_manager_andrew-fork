"""
YAML configuration validation utilities for Azentiq Memory Manager.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Union, Tuple, Optional
import jsonschema

from utils.schemas import load_schema


class ConfigValidator:
    """Validator for YAML configuration files."""
    
    def __init__(self, schema_name: str = "memory_config_schema"):
        """Initialize the validator with a schema.
        
        Args:
            schema_name: Name of the schema file without extension
        """
        self.schema = load_schema(schema_name)
    
    def validate_yaml_file(self, yaml_file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """Validate a YAML file against the schema.
        
        Args:
            yaml_file_path: Path to the YAML file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(yaml_file_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            return self.validate_dict(yaml_data)
        except FileNotFoundError:
            return False, f"File not found: {yaml_file_path}"
        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def validate_yaml_string(self, yaml_string: str) -> Tuple[bool, Optional[str]]:
        """Validate a YAML string against the schema.
        
        Args:
            yaml_string: YAML content as a string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            yaml_data = yaml.safe_load(yaml_string)
            return self.validate_dict(yaml_data)
        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate a dictionary against the schema.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            jsonschema.validate(instance=data, schema=self.schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, f"Validation error: {e.message}"
    
    @staticmethod
    def generate_example_config() -> Dict[str, Any]:
        """Generate an example configuration.
        
        Returns:
            Example configuration as a dictionary
        """
        return {
            "version": "1.0",
            "application": {
                "name": "Example Agent",
                "default_model": "gpt-4",
                "global_token_limit": 8192
            },
            "memory_tiers": {
                "short_term": {
                    "ttl_seconds": 1800,
                    "default_importance": 0.5
                },
                "working": {
                    "ttl_seconds": None,
                    "default_importance": 0.7
                }
            },
            "components": [
                {
                    "id": "planner",
                    "type": "agent",
                    "model": "gpt-4-turbo",
                    "token_limit": 8000,
                    "memory_allocation": {
                        "short_term": 0.2,
                        "working": 0.6,
                        "long_term": 0.2
                    },
                    "memory_priority": "high",
                    "framework": "langchain"
                },
                {
                    "id": "executor",
                    "type": "agent",
                    "token_limit": 4000,
                    "memory_allocation": {
                        "short_term": 0.3,
                        "working": 0.7
                    },
                    "memory_priority": "medium",
                    "framework": "app"
                }
            ],
            "workflows": [
                {
                    "id": "main_workflow",
                    "components": ["planner", "executor"],
                    "memory_inheritance": [
                        {
                            "from": "planner",
                            "to": "executor",
                            "metadata_filter": {
                                "type": "plan_step"
                            }
                        }
                    ]
                }
            ],
            "memory_policies": [
                {
                    "name": "token_overflow",
                    "action": "prioritize_by_importance"
                }
            ]
        }
    
    def save_example_config(self, output_path: Union[str, Path]) -> None:
        """Save an example configuration to a YAML file.
        
        Args:
            output_path: Path to save the example configuration
        """
        example = self.generate_example_config()
        with open(output_path, 'w') as f:
            yaml.dump(example, f, default_flow_style=False, sort_keys=False)


def validate_config_file(yaml_file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
    """Convenience function to validate a YAML configuration file.
    
    Args:
        yaml_file_path: Path to the YAML file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = ConfigValidator()
    return validator.validate_yaml_file(yaml_file_path)


def generate_example_config_file(output_path: Union[str, Path]) -> None:
    """Convenience function to generate an example configuration file.
    
    Args:
        output_path: Path to save the example configuration
    """
    validator = ConfigValidator()
    validator.save_example_config(output_path)
