"""
Test script to verify import paths for Google ADK after GitHub installation.
"""
import sys
import os

print("Python version:", sys.version)
print("Testing ADK imports...")

try:
    import google.adk
    print("✓ Successfully imported google.adk")
    print(f"  Module located at: {google.adk.__file__}")
    
    # Try to import agent module
    try:
        import google.adk.agent
        print("✓ Successfully imported google.adk.agent")
        print(f"  Module located at: {google.adk.agent.__file__}")
        
        # Try to import session
        try:
            import google.adk.agent.session
            print("✓ Successfully imported google.adk.agent.session")
            print(f"  Module located at: {google.adk.agent.session.__file__}")
            print("  Available attributes:", dir(google.adk.agent.session))
        except ImportError as e:
            print("✗ Failed to import google.adk.agent.session:", str(e))
    except ImportError as e:
        print("✗ Failed to import google.adk.agent:", str(e))
        
    # Try alternate import paths from GitHub examples
    try:
        import google.adk.agents
        print("✓ Successfully imported google.adk.agents")
        print(f"  Module located at: {google.adk.agents.__file__}")
    except ImportError as e:
        print("✗ Failed to import google.adk.agents:", str(e))
        
    # Check all submodules
    print("\nAvailable submodules in google.adk:")
    for name in dir(google.adk):
        if not name.startswith('_'):  # Skip private modules
            print(f"  - {name}")
            
    # List all files in the google.adk package directory
    adk_dir = os.path.dirname(google.adk.__file__)
    print(f"\nFiles in {adk_dir}:")
    for item in os.listdir(adk_dir):
        print(f"  - {item}")
        
except ImportError as e:
    print("✗ Failed to import google.adk:", str(e))
    print("The Google ADK package may not be installed correctly.")

print("\nFinished testing imports.")
