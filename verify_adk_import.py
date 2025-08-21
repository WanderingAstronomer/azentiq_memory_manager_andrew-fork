"""
Simple script to verify Google ADK imports and print information to file.
"""
import sys
import os

# Write results to a file to avoid console truncation issues
with open("adk_verify_results.txt", "w") as f:
    def write(msg):
        f.write(msg + "\n")
        f.flush()  # Force flush to ensure output is written
    
    write(f"Python version: {sys.version}")
    write("Attempting to import Google ADK modules...")
    
    try:
        import google.adk
        write("SUCCESS: Imported google.adk")
        write(f"Version: {getattr(google.adk, '__version__', 'Unknown')}")
        write(f"Location: {getattr(google.adk, '__file__', 'Unknown')}")
        
        # Try to import specific components we need
        try:
            from google.adk.agent import session
            write("SUCCESS: Imported google.adk.agent.session")
            write(f"Location: {session.__file__}")
            
            if hasattr(session, 'Session'):
                write("SUCCESS: Found Session class")
            else:
                write("ERROR: Session class not found in google.adk.agent.session")
                write(f"Available attributes: {[a for a in dir(session) if not a.startswith('_')]}")
        except ImportError as e:
            write(f"ERROR importing session: {str(e)}")
        
        try:
            from google.adk.agent import memory
            write("SUCCESS: Imported google.adk.agent.memory")
            write(f"Location: {memory.__file__}")
            
            if hasattr(memory, 'BaseMemoryService'):
                write("SUCCESS: Found BaseMemoryService class")
            else:
                write("ERROR: BaseMemoryService class not found in google.adk.agent.memory")
                write(f"Available attributes: {[a for a in dir(memory) if not a.startswith('_')]}")
        except ImportError as e:
            write(f"ERROR importing memory: {str(e)}")
            
    except ImportError as e:
        write(f"ERROR importing google.adk: {str(e)}")

print("Verification complete. See adk_verify_results.txt for results.")
