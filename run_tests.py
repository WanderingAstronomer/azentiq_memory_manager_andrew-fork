#!/usr/bin/env python
"""
Test runner for Azentiq Memory Manager.

This script discovers and runs all unit tests in the project.
Run with:
    python run_tests.py             # Run all tests
    python run_tests.py -v          # Verbose output
    python run_tests.py module_name # Run specific test module
"""

import unittest
import sys
import os
import importlib.util

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Check Python version
import platform
python_version = tuple(map(int, platform.python_version_tuple()))
if python_version < (3, 11):
    print(f"Warning: This project requires Python 3.11+. You are using Python {platform.python_version()}.")


def import_module_from_file(module_name, file_path):
    """Import a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def ensure_module_can_be_imported(module_name):
    """Check if module can be imported and fix path if needed."""
    try:
        importlib.import_module(module_name)
        return True
    except ModuleNotFoundError:
        # Module not found, try to fix path
        parts = module_name.split('.')
        if len(parts) > 1:
            parent_module = '.'.join(parts[:-1])
            try:
                importlib.import_module(parent_module)
                return True
            except ModuleNotFoundError:
                # Parent module not found, try to fix path
                potential_path = os.path.join(project_root, *parts[:-1])
                if os.path.exists(potential_path):
                    if os.path.exists(os.path.join(potential_path, '__init__.py')):
                        sys.path.insert(0, os.path.dirname(potential_path))
                        return True
        return False


if __name__ == "__main__":
    # Ensure core modules can be imported
    modules_to_check = ['core', 'storage', 'utils']
    for module in modules_to_check:
        ensure_module_can_be_imported(module)
    
    # Set up test discovery
    test_loader = unittest.TestLoader()
    
    if len(sys.argv) > 1 and sys.argv[1] != '-v':
        # If a specific test module is provided, run only that
        module_name = sys.argv[1]
        print(f"Running tests for module: {module_name}")
        
        # Try to load the specified tests
        try:
            suite = test_loader.loadTestsFromName(f"tests.{module_name}")
        except ImportError:
            try:
                # Try with direct module name
                suite = test_loader.loadTestsFromName(module_name)
            except ImportError:
                print(f"Error: Could not find test module '{module_name}'")
                sys.exit(1)
    else:
        # Otherwise discover all tests
        print("Discovering and running all tests...")
        suite = test_loader.discover('tests')
    
    # Create test runner
    verbosity = 2 if '-v' in sys.argv else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    
    # Run tests
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())
