#!/usr/bin/env python
"""
Simple test runner for Azentiq Memory Manager.
Run a single test module directly, with proper path configuration.

Usage:
    python run_single_test.py tests/utils/token_budget/test_estimator.py
"""

import sys
import os
import importlib
import unittest

def run_test_file(test_file):
    """Run tests from a single file."""
    # Add project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Convert file path to module path
    if test_file.endswith('.py'):
        test_file = test_file[:-3]
    module_path = test_file.replace(os.path.sep, '.')
    
    # Try to import the module
    try:
        test_module = importlib.import_module(module_path)
        
        # Run the tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Return success/failure
        return result.wasSuccessful()
    except ImportError as e:
        print(f"Error importing test module {module_path}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_single_test.py <test_file_path>")
        sys.exit(1)
        
    test_file = sys.argv[1]
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} not found.")
        sys.exit(1)
        
    success = run_test_file(test_file)
    sys.exit(0 if success else 1)
