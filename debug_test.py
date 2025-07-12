import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from core.memory_manager import MemoryManager

class DebugTest(unittest.TestCase):
    """Test to debug specific failures."""
    
    def test_redis_store_init_params(self):
        """Debug RedisStore initialization parameters."""
        # Mock RedisStore
        redis_store_mock = MagicMock()
        
        # Create patch for RedisStore
        with patch('core.memory_manager.RedisStore', return_value=redis_store_mock) as redis_mock_class:
            # Create MemoryManager with framework specified
            manager = MemoryManager(framework="test_framework")
            
            # Print actual call arguments
            print("\nActual call args to RedisStore:", redis_mock_class.call_args)
            
            # Test with custom Redis URL
            manager2 = MemoryManager(redis_url="redis://custom:6380")
            print("Second call args to RedisStore:", redis_mock_class.call_args)
            
            # Verify all calls
            print("All calls to RedisStore:", redis_mock_class.call_args_list)

if __name__ == "__main__":
    unittest.main()
