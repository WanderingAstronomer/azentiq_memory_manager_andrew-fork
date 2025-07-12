"""Unit tests for the RedisStore class."""

import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import json
import uuid

# Fix imports to work with both pytest and unittest discovery
import sys
import os
# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from storage.redis_store import RedisStore
from core.interfaces import Memory, MemoryTier


class TestRedisStore(unittest.TestCase):
    """Test suite for RedisStore class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a patch for redis.from_url so we don't connect to a real Redis server
        self.redis_mock = MagicMock()
        self.patcher = patch('storage.redis_store.redis.from_url', return_value=self.redis_mock)
        self.patcher.start()
        
        # Create a RedisStore instance with default parameters
        self.store = RedisStore(
            redis_url="redis://localhost:6379",
            prefix="test_memory:",
            expire_seconds=3600,
            framework="test_framework"
        )
        
        # Create a test memory for reuse
        self.test_memory = Memory(
            memory_id="test123",
            content="Test memory content",
            metadata={"source": "test"},
            importance=0.8,
            tier=MemoryTier.WORKING,
            created_at="2023-07-11T15:30:00Z",
            last_accessed_at="2023-07-11T15:30:00Z"
        )
        
        # Set a test session ID
        self.test_session_id = "test_session"
        
        # Set component context for testing
        self.store.set_context("test_component")
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop the patcher
        self.patcher.stop()
    
    def test_init(self):
        """Test initialization with different parameters."""
        # Test default init
        store = RedisStore()
        self.assertEqual(store.prefix, "memory:")
        self.assertIsNone(store.expire_seconds)
        self.assertEqual(store.framework, "app")
        self.assertIsNone(store.current_component_id)
        
        # Test custom init
        store = RedisStore(
            redis_url="redis://custom:6380",
            prefix="custom_prefix:",
            expire_seconds=7200,
            framework="langchain"
        )
        self.assertEqual(store.prefix, "custom_prefix:")
        self.assertEqual(store.expire_seconds, 7200)
        self.assertEqual(store.framework, "langchain")
        self.assertIsNone(store.current_component_id)
    
    def test_set_context(self):
        """Test setting component context."""
        # Initialize the current_component_id attribute if it doesn't exist
        if not hasattr(self.store, 'current_component_id'):
            self.store.current_component_id = None
            
        # Test setting component ID
        self.store.set_context("new_component")
        self.assertEqual(self.store.current_component_id, "new_component")
        
        # Test with None - this should not change the current value since
        # the implementation only sets the value when component_id is not None
        self.store.set_context(None)
        # The actual implementation does not set to None when None is passed
        self.assertEqual(self.store.current_component_id, "new_component")
    
    def test_get_namespace(self):
        """Test namespace generation."""
        # Test with all parameters
        namespace = self.store._get_namespace(
            memory_id="test123",
            tier_str="working",
            session_id="session123"
        )
        expected = "working:session123:test_framework:test_component:test123"
        self.assertEqual(namespace, expected)
        
        # Test with missing session ID (should use 'global')
        namespace = self.store._get_namespace(
            memory_id="test123",
            tier_str="working",
            session_id=None
        )
        expected = "working:global:test_framework:test_component:test123"
        self.assertEqual(namespace, expected)
        
        # Test without component ID set
        self.store.current_component_id = None
        namespace = self.store._get_namespace(
            memory_id="test123",
            tier_str="working",
            session_id="session123"
        )
        expected = "working:session123:test_framework:main:test123"
        self.assertEqual(namespace, expected)
    
    def test_get_key(self):
        """Test key generation with and without namespacing."""
        # Test namespaced key
        key = self.store._get_key(
            memory_id="test123",
            tier_str="working",
            session_id="session123"
        )
        expected = "test_memory:working:session123:test_framework:test_component:test123"
        self.assertEqual(key, expected)
        
        # Test legacy key format (without tier)
        key = self.store._get_key(
            memory_id="test123",
            tier_str=None
        )
        expected = "test_memory:test123"
        self.assertEqual(key, expected)
    
    def test_add_memory(self):
        """Test adding a memory with proper namespacing."""
        # Reset mocks for clean state
        self.redis_mock.setex.reset_mock()
        self.redis_mock.set.reset_mock()
        
        # Create a fresh copy of test memory to ensure clean state
        test_memory = Memory(
            memory_id="test123",
            content="Test memory content",
            metadata={"source": "test"},
            importance=0.8,
            tier=MemoryTier.WORKING,
            created_at="2023-07-11T15:30:00Z",
            last_accessed_at="2023-07-11T15:30:00Z"
        )
        
        # Create a mock for memory.to_dict() to control the exact output
        memory_dict = {
            "memory_id": "test123",
            "content": "Test memory content",
            "metadata": {"source": "test"},
            "importance": 0.8,
            "tier": "working",
            "created_at": "2023-07-11T15:30:00Z",
            "last_accessed_at": "2023-07-11T15:30:00Z"
        }
        
        # Patch the to_dict method
        with patch.object(Memory, 'to_dict', return_value=memory_dict):
            # Add memory
            result = self.store.add(test_memory, self.test_session_id)
            
            # Check that the Redis client was called with the correct arguments
            expected_key = "test_memory:working:test_session:test_framework:test_component:test123"
            expected_value = json.dumps(memory_dict)
            
            # Check the key was set with expiration
            self.redis_mock.setex.assert_called_once_with(
                expected_key, self.store.expire_seconds, expected_value
            )
            
            # Verify the return value is the memory_id
            self.assertEqual(result, test_memory.memory_id)
    
    def test_add_memory_no_id(self):
        """Test adding a memory with no ID (should generate one)."""
        # Reset mocks
        self.redis_mock.setex.reset_mock()
        self.redis_mock.set.reset_mock()
        
        # Create memory with no ID
        memory_no_id = Memory(
            memory_id=None,
            content="Memory without ID",
            metadata={},
            importance=0.5,
            tier=MemoryTier.SHORT_TERM
        )
        
        # Patch UUID generation to use a predictable value
        test_uuid = "generated-uuid-123"
        with patch('storage.redis_store.uuid.uuid4', return_value=test_uuid):
            # Mock to_dict to return a stable dict for testing
            expected_memory_dict = {
                "memory_id": test_uuid,  # The UUID will be applied
                "content": "Memory without ID",
                "metadata": {},
                "importance": 0.5,
                "tier": "short_term",
                "created_at": None,  # Assuming these default to None
                "last_accessed_at": None
            }
            
            with patch.object(Memory, 'to_dict', return_value=expected_memory_dict):
                # Add memory
                returned_id = self.store.add(memory_no_id, self.test_session_id)
                
                # Check that the UUID was applied and returned
                self.assertEqual(memory_no_id.memory_id, test_uuid)
                self.assertEqual(returned_id, test_uuid)
                
                # Verify the Redis call
                self.assertEqual(self.redis_mock.setex.call_count, 1)
                call_args = self.redis_mock.setex.call_args[0]
                
                # Check the key contains our expected values
                expected_key = f"test_memory:short_term:test_session:test_framework:test_component:{test_uuid}"
                self.assertEqual(call_args[0], expected_key)
                
                # Verify the value is correctly serialized
                self.assertEqual(call_args[2], json.dumps(expected_memory_dict))
    
    def test_get_memory_found(self):
        """Test retrieving a memory that exists."""
        # Set up a mock serialized representation to avoid isoformat() errors
        serialized_dict = {
            "memory_id": self.test_memory.memory_id,
            "content": self.test_memory.content,
            "metadata": self.test_memory.metadata,
            "tier": self.test_memory.tier.value,
            "ttl": self.test_memory.ttl,
            "created_at": self.test_memory.created_at,  # Already a string
            "updated_at": self.test_memory.created_at,  # Use same value for simplicity
            "last_accessed_at": self.test_memory.last_accessed_at,  # Already a string
            "importance": self.test_memory.importance
        }
        serialized_memory = json.dumps(serialized_dict)
        self.redis_mock.get.return_value = serialized_memory
        
        # Get the memory
        memory = self.store.get(
            memory_id="test123",
            tier_str="working",
            session_id=self.test_session_id
        )
        
        # Check the memory was retrieved correctly
        self.assertIsNotNone(memory)
        self.assertEqual(memory.memory_id, "test123")
        self.assertEqual(memory.content, "Test memory content")
        
        # Verify Redis was queried with the correct key
        expected_key = "test_memory:working:test_session:test_framework:test_component:test123"
        self.redis_mock.get.assert_called_with(expected_key)
        
        # Verify the memory was updated with a new last_accessed_at timestamp
        # We're using setex since the test has expire_seconds set
        self.redis_mock.setex.assert_called_once()
    
    def test_get_memory_not_found_fallback(self):
        """Test retrieving a memory with fallback to legacy key."""
        # Create a mock serialized representation to avoid isoformat() errors
        serialized_dict = {
            "memory_id": self.test_memory.memory_id,
            "content": self.test_memory.content,
            "metadata": self.test_memory.metadata,
            "tier": self.test_memory.tier.value,
            "ttl": self.test_memory.ttl,
            "created_at": self.test_memory.created_at,  # Already a string
            "updated_at": self.test_memory.created_at,  # Use same value for simplicity
            "last_accessed_at": self.test_memory.last_accessed_at,  # Already a string
            "importance": self.test_memory.importance
        }
        serialized_memory = json.dumps(serialized_dict)
        
        # Reset call history
        self.redis_mock.get.reset_mock()
        
        # In the actual implementation, once a key is found, it stops searching.
        # So we need to modify our test to reflect this behavior.
        # Only the legacy key should be checked since it returns the memory.
        self.redis_mock.get.return_value = serialized_memory
        
        # Test with no tier specified - should find it using the legacy key format
        memory = self.store.get(
            memory_id="test123", 
            tier_str=None,  # Explicitly set to None
            session_id=self.test_session_id
        )
        
        # Check the memory was found
        self.assertIsNotNone(memory)
        self.assertEqual(memory.memory_id, "test123")
        self.assertEqual(memory.content, "Test memory content")
        
        # Verify Redis was called with the legacy key format first
        # This is the key format when no tier is specified: prefix + memory_id
        legacy_key = "test_memory:test123"
        self.redis_mock.get.assert_called_once_with(legacy_key)
        
        # Now test the fallback mechanism with legacy key not found
        self.redis_mock.get.reset_mock()
        
        # Setup a side_effect that returns None for legacy key but data for one of the tier keys
        def mock_get_with_fallback(key):
            if key == "test_memory:working:test_session:test_framework:test_component:test123":
                return serialized_memory
            return None
            
        self.redis_mock.get.side_effect = mock_get_with_fallback
        
        # Get the memory again
        memory = self.store.get(memory_id="test123", session_id=self.test_session_id)
        
        # Check the expected calls in order
        expected_calls = [
            call("test_memory:test123"),  # Legacy key
            call("test_memory:short_term:test_session:test_framework:test_component:test123"),  # First tier
            call("test_memory:working:test_session:test_framework:test_component:test123"),  # Second tier
        ]
        self.redis_mock.get.assert_has_calls(expected_calls, any_order=False)
        
        # Third tier (long_term) should not be called since it would find the memory in working tier
    
    def test_get_memory_not_found(self):
        """Test retrieving a memory that does not exist."""
        # Set up mock to return None for all keys
        self.redis_mock.get.return_value = None
        
        # Get a non-existent memory
        memory = self.store.get(
            memory_id="nonexistent",
            tier_str="working",
            session_id=self.test_session_id
        )
        
        # Memory should not be found
        self.assertIsNone(memory)
        
        # Verify Redis was queried with the expected key
        expected_key = "test_memory:working:test_session:test_framework:test_component:nonexistent"
        self.redis_mock.get.assert_any_call(expected_key)
        
        # Only one call should be made since tier_str is provided (no fallback needed)
        self.assertEqual(self.redis_mock.get.call_count, 1)
    
    def test_update_memory(self):
        """Test updating an existing memory."""
        # Reset any previous calls
        self.redis_mock.set.reset_mock()
        self.redis_mock.setex.reset_mock()
        
        # We need to patch Memory.to_dict to handle string dates
        # Create a mock serialized representation
        serialized_memory = {
            "memory_id": self.test_memory.memory_id,
            "content": "Updated content",  # The updated content
            "metadata": self.test_memory.metadata,
            "tier": self.test_memory.tier.value,
            "ttl": self.test_memory.ttl,
            "created_at": self.test_memory.created_at,  # Already a string
            "updated_at": self.test_memory.created_at,  # Use same value for simplicity 
            "last_accessed_at": self.test_memory.last_accessed_at,  # Already a string
            "importance": self.test_memory.importance
        }
        
        # Patch Memory.to_dict to return our serialized representation
        with patch('core.interfaces.Memory.to_dict', return_value=serialized_memory):
            # Update memory
            self.test_memory.content = "Updated content"
            self.store.update(self.test_memory, self.test_session_id)
            
            # Check Redis was called with the correct arguments
            expected_key = "test_memory:working:test_session:test_framework:test_component:test123"
            expected_value = json.dumps(serialized_memory)
            
            # Should use setex since we have expire_seconds set in the fixture
            self.redis_mock.setex.assert_called_once_with(
                expected_key, self.store.expire_seconds, expected_value
            )
            self.redis_mock.set.assert_not_called()
    
    def test_delete_memory_with_tier(self):
        """Test deleting a memory with tier information."""
        # Delete memory
        self.store.delete(
            memory_id="test123",
            tier_str="working",
            session_id=self.test_session_id
        )
        
        # Check Redis delete was called with the correct key
        expected_key = "test_memory:working:test_session:test_framework:test_component:test123"
        self.redis_mock.delete.assert_called_once_with(expected_key)
    
    def test_delete_memory_without_tier(self):
        """Test deleting a memory without tier information (should try all tiers)."""
        # Delete memory without specifying tier
        self.store.delete(
            memory_id="test123",
            session_id=self.test_session_id
        )
        
        # Should try deleting from legacy format and all tiers
        expected_calls = [
            call("test_memory:test123"),  # Legacy key
            call("test_memory:short_term:test_session:test_framework:test_component:test123"),
            call("test_memory:working:test_session:test_framework:test_component:test123"),
            call("test_memory:long_term:test_session:test_framework:test_component:test123")
        ]
        
        self.redis_mock.delete.assert_has_calls(expected_calls)
        self.assertEqual(self.redis_mock.delete.call_count, 4)
    
    def test_list_memories(self):
        """Test listing memories with filtering."""
        # Mock scan to return keys
        self.redis_mock.scan.return_value = (0, [
            b"test_memory:working:test_session:test_framework:test_component:key1",
            b"test_memory:working:test_session:test_framework:test_component:key2"
        ])
        
        # Mock mget to return serialized memories
        memory1 = Memory(memory_id="key1", content="Content 1", tier=MemoryTier.WORKING)
        memory2 = Memory(memory_id="key2", content="Content 2", tier=MemoryTier.WORKING)
        self.redis_mock.mget.return_value = [
            json.dumps(memory1.to_dict()),
            json.dumps(memory2.to_dict())
        ]
        
        # List memories
        memories = self.store.list(
            tier_str="working",
            session_id=self.test_session_id,
            limit=10
        )
        
        # Check results
        self.assertEqual(len(memories), 2)
        self.assertEqual(memories[0].memory_id, "key1")
        self.assertEqual(memories[1].memory_id, "key2")
        
        # Verify scan was called with the correct pattern
        expected_pattern = "test_memory:working:test_session:test_framework:test_component:*"
        self.redis_mock.scan.assert_called_with(
            cursor=0, match=expected_pattern, count=1000
        )
    
    def test_list_memories_different_patterns(self):
        """Test list pattern generation with different filter combinations."""
        # Set up for empty return
        self.redis_mock.scan.return_value = (0, [])
        self.redis_mock.mget.return_value = []
        
        # 1. With tier only
        self.store.list(tier_str="working")
        expected_pattern = "test_memory:working:*"
        self.redis_mock.scan.assert_called_with(
            cursor=0, match=expected_pattern, count=1000
        )
        
        # 2. With session only
        self.store.list(session_id="session123")
        expected_pattern = "test_memory:*:session123:*"
        self.redis_mock.scan.assert_called_with(
            cursor=0, match=expected_pattern, count=1000
        )
        
        # 3. With no filters
        self.store.list()
        expected_pattern = "test_memory:*"
        self.redis_mock.scan.assert_called_with(
            cursor=0, match=expected_pattern, count=1000
        )
    
    def test_search_by_metadata(self):
        """Test searching memories by metadata."""
        # Set up test memories with different metadata
        memory1 = Memory(
            memory_id="key1", 
            content="Content 1", 
            metadata={"tag": "important", "category": "work"},
            tier=MemoryTier.WORKING
        )
        memory2 = Memory(
            memory_id="key2", 
            content="Content 2", 
            metadata={"tag": "regular", "category": "work"},
            tier=MemoryTier.WORKING
        )
        
        # Mock list to return test memories
        with patch.object(self.store, 'list', return_value=[memory1, memory2]):
            # Search for memories with specific metadata
            results = self.store.search_by_metadata(
                query={"category": "work", "tag": "important"},
                limit=10,
                tier_str="working"
            )
            
            # Only memory1 should match
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].memory_id, "key1")
            
            # Verify list was called with the right arguments
            self.store.list.assert_called_with(
                limit=10000, tier_str="working", session_id=None
            )
    
    def test_search_by_metadata_with_session(self):
        """Test metadata search using session_id from query."""
        # Mock list to verify call arguments
        with patch.object(self.store, 'list', return_value=[]):
            # Search with session_id in query
            self.store.search_by_metadata(
                query={"session_id": "session123", "category": "work"},
                tier_str="working"
            )
            
            # Verify session_id was extracted and passed to list
            self.store.list.assert_called_with(
                limit=10000, tier_str="working", session_id="session123"
            )


if __name__ == "__main__":
    unittest.main()
