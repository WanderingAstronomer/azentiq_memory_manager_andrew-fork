import sys
import pytest

def run_tests():
    """Run all tests and print failing test names."""
    result = pytest.main(['tests/test_memory_manager.py', '-v'])
    sys.exit(result)

if __name__ == "__main__":
    run_tests()
