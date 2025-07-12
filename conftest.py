"""
Configuration file for pytest.
This file helps Python find the packages in our project structure.
"""

import os
import sys

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
