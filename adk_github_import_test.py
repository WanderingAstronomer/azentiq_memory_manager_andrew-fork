"""
Test script to verify imports from the Google ADK GitHub repository.
"""
import sys
import os
from datetime import datetime

# Set up output file
output_file = "adk_github_import_results.txt"
if os.path.exists(output_file):
    os.remove(output_file)

def log(message):
    """Write message to both output file and console."""
    print(message)
    with open(output_file, 'a') as f:
        f.write(f"{message}\n")

log("=== Google ADK GitHub Import Test ===")
log(f"Python version: {sys.version}")
log(f"Current time: {datetime.now().isoformat()}")
log("")

# Test imports that should be available from Google ADK
import_tests = [
    {
        "import": "import google.adk",
        "check_attr": ["__version__"],
        "description": "Base ADK package"
    },
    {
        "import": "from google.adk import agent",
        "check_attr": ["agent"],
        "description": "ADK agent module"
    },
    {
        "import": "from google.adk import agents",
        "check_attr": ["agents"],
        "description": "ADK agents module"
    },
    {
        "import": "from google.adk.agent import session",
        "check_attr": ["session", "Session"],
        "description": "ADK session module"
    },
    {
        "import": "from google.adk.agent import memory",
        "check_attr": ["memory", "BaseMemoryService"],
        "description": "ADK memory module"
    },
    {
        "import": "from google.adk.agent.memory import BaseMemoryService",
        "check_attr": ["BaseMemoryService"],
        "description": "ADK BaseMemoryService class"
    },
    {
        "import": "from google.adk.agent.session import Session",
        "check_attr": ["Session"],
        "description": "ADK Session class"
    }
]

# Global namespace for evaluating imports
namespace = {}

# Test each import
for test in import_tests:
    try:
        log(f"Testing: {test['description']} - {test['import']}")
        exec(test["import"], namespace)
        log("✓ Import successful")
        
        # Check for expected attributes
        for attr in test["check_attr"]:
            if attr in namespace:
                log(f"  ✓ Found {attr}: {type(namespace[attr])}")
                
                # If this is a module, list its contents
                if attr in namespace and hasattr(namespace[attr], "__file__"):
                    log(f"    Location: {namespace[attr].__file__}")
                    
                    # List all non-private attributes
                    public_attrs = [a for a in dir(namespace[attr]) if not a.startswith("_")]
                    log(f"    Public attributes: {', '.join(public_attrs[:10])}")
                    if len(public_attrs) > 10:
                        log(f"    ...and {len(public_attrs) - 10} more")
            else:
                log(f"  ✗ Attribute {attr} not found")
        log("")
    except ImportError as e:
        log(f"✗ Import failed: {str(e)}")
    except Exception as e:
        log(f"✗ Error: {str(e)}")
    log("")

log("=== Test Complete ===")
log(f"Results saved to {output_file}")
