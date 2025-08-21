"""
Simple test to verify Google ADK import paths.
"""
import os
import sys

# Set up output file
output_file = "simple_adk_test_results.txt"
if os.path.exists(output_file):
    os.remove(output_file)

def log(message):
    """Write message to output file."""
    with open(output_file, 'a') as f:
        f.write(message + "\n")
    print(message)

log("=== Simple Google ADK Import Test ===")
log(f"Python version: {sys.version}")

# Try importing from various paths
import_paths = [
    # From GitHub examples
    ("google.adk.agents", "Agent"),
    ("google.adk.tools", "google_search"),
    
    # Our original paths
    ("google.adk.agent.session", "Session"),
    ("google.adk.agent.memory", "BaseMemoryService"),
    
    # Alternative paths
    ("google.adk", "agents"),
    ("google.adk", "agent"),
]

for module_path, attribute in import_paths:
    try:
        log(f"\nTrying to import '{attribute}' from '{module_path}'...")
        
        # Try to import the module
        module = __import__(module_path, fromlist=[attribute])
        log(f"✓ Successfully imported module '{module_path}'")
        log(f"  Module file: {getattr(module, '__file__', 'Not available')}")
        
        # Check if the attribute exists
        if hasattr(module, attribute):
            log(f"✓ Found '{attribute}' in '{module_path}'")
            attr_value = getattr(module, attribute)
            log(f"  Type: {type(attr_value)}")
        else:
            log(f"✗ '{attribute}' not found in '{module_path}'")
            log(f"  Available attributes: {[a for a in dir(module) if not a.startswith('_')]}")
    except ImportError as e:
        log(f"✗ Failed to import '{module_path}': {str(e)}")
    except Exception as e:
        log(f"✗ Error: {str(e)}")

log("\n=== Test Complete ===")
log(f"Results saved to {output_file}")
