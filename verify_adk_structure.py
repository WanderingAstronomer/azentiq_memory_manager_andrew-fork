"""
Script to verify Google ADK imports using the correct package structure.
"""
import sys
import os

# Write results to a file to avoid console truncation issues
with open("adk_structure_verify.txt", "w") as f:
    def write(msg):
        f.write(msg + "\n")
        f.flush()  # Force flush to ensure output is written
    
    write(f"Python version: {sys.version}")
    write("Verifying Google ADK module structure...")
    
    try:
        import google.adk
        write("SUCCESS: Imported google.adk")
        write(f"Version: {getattr(google.adk, '__version__', 'Unknown')}")
        write(f"Location: {getattr(google.adk, '__file__', 'Unknown')}")
        
        # Test the actual structure we found in the repository
        
        # Test agents module (plural)
        try:
            from google.adk import agents
            write("SUCCESS: Imported google.adk.agents")
            write(f"Location: {agents.__file__}")
            write(f"Public attributes: {[a for a in dir(agents) if not a.startswith('_')][:10]}")
            
            # Try to find the Agent class
            if hasattr(agents, 'Agent'):
                write("SUCCESS: Found Agent class in google.adk.agents")
            else:
                write("NOTE: Agent class not directly in google.adk.agents")
                
                # Check if it might be in a submodule
                submodules = [a for a in dir(agents) if not a.startswith('_') and hasattr(getattr(agents, a), '__file__')]
                write(f"Submodules: {submodules}")
        except ImportError as e:
            write(f"ERROR importing agents: {str(e)}")
        
        # Test memory module
        try:
            from google.adk import memory
            write("SUCCESS: Imported google.adk.memory")
            write(f"Location: {memory.__file__}")
            write(f"Public attributes: {[a for a in dir(memory) if not a.startswith('_')][:10]}")
            
            # Try to find BaseMemoryService
            memory_classes = [a for a in dir(memory) if not a.startswith('_') and isinstance(getattr(memory, a), type)]
            write(f"Memory classes: {memory_classes}")
            
            if 'BaseMemoryService' in memory_classes:
                write("SUCCESS: Found BaseMemoryService in google.adk.memory")
            else:
                write("NOTE: BaseMemoryService not directly in google.adk.memory")
        except ImportError as e:
            write(f"ERROR importing memory: {str(e)}")
        
        # Test sessions module
        try:
            from google.adk import sessions
            write("SUCCESS: Imported google.adk.sessions")
            write(f"Location: {sessions.__file__}")
            write(f"Public attributes: {[a for a in dir(sessions) if not a.startswith('_')][:10]}")
            
            # Try to find Session class
            session_classes = [a for a in dir(sessions) if not a.startswith('_') and isinstance(getattr(sessions, a), type)]
            write(f"Session classes: {session_classes}")
            
            if 'Session' in session_classes:
                write("SUCCESS: Found Session class in google.adk.sessions")
            else:
                write("NOTE: Session class not directly in google.adk.sessions")
        except ImportError as e:
            write(f"ERROR importing sessions: {str(e)}")
            
    except ImportError as e:
        write(f"ERROR importing google.adk: {str(e)}")

print("Verification complete. See adk_structure_verify.txt for results.")
