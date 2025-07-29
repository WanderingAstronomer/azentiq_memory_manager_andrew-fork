import os
import sys

def add_project_root_to_path():
    """
    Add the project root directory to the Python path to enable core module imports.
    This should be imported at the top of any file that needs to import from core modules.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added project root to Python path: {project_root}")
    return project_root
