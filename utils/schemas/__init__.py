"""
JSON Schema definitions for Azentiq Memory Manager configurations.
"""

import os
import json
from pathlib import Path

# Get the path to the schemas directory
SCHEMAS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

def get_schema_path(schema_name: str) -> Path:
    """Get the path to a schema file.
    
    Args:
        schema_name: Name of the schema file without extension
        
    Returns:
        Path to the schema file
    """
    return SCHEMAS_DIR / f"{schema_name}.json"

def load_schema(schema_name: str) -> dict:
    """Load a schema from a file.
    
    Args:
        schema_name: Name of the schema file without extension
        
    Returns:
        The schema as a dictionary
    """
    schema_path = get_schema_path(schema_name)
    with open(schema_path, "r") as f:
        return json.load(f)
