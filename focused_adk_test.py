"""
Focused test to verify Google ADK import paths with console output.
"""
import sys

print("=== Focused Google ADK Import Test ===")
print(f"Python version: {sys.version}")

# Try importing from various paths
import_paths = [
    ("google.adk", ["agents", "agent", "tools"]),
    ("google.adk.agents", ["Agent"]),
    ("google.adk.tools", ["google_search"]),
    ("google.adk.agent", ["session", "memory"]),
    ("google.adk.agent.session", ["Session"]),
    ("google.adk.agent.memory", ["BaseMemoryService"])
]

for base_module, sub_items in import_paths:
    print(f"\nTrying base module: {base_module}")
    try:
        # Try to import the base module
        module = __import__(base_module, fromlist=sub_items)
        print(f"✓ Imported {base_module}")
        
        # Check for sub-modules or attributes
        for item in sub_items:
            try:
                if hasattr(module, item):
                    attr = getattr(module, item)
                    print(f"  ✓ Found {item}: {type(attr)}")
                else:
                    print(f"  ✗ {item} not found")
            except Exception as e:
                print(f"  ✗ Error checking {item}: {str(e)[:50]}")
    except ImportError as e:
        print(f"✗ Failed: {str(e)[:50]}")
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")

print("\n=== Test Complete ===")
