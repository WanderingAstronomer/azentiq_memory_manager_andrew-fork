"""Unit tests for the MemoryManager class."""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uuid
from datetime import datetime

from core.memory_manager import MemoryManager
from core.interfaces import Memory, MemoryTier
from storage.redis_store import RedisStore
from utils.token_budget import TokenBudgetManager


class TestMemoryManager(unittest.TestCase):
    """Test suite for MemoryManager class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mocks for RedisStore and TokenBudgetManager
        self.redis_patcher = patch('core.memory_manager.RedisStore')
        self.token_patcher = patch('core.memory_manager.TokenBudgetManager')
        
        self.redis_mock_class = self.redis_patcher.start()
        self.token_mock_class = self.token_patcher.start()
        
        # Create mock instances
        self.redis_store_mock = MagicMock()
        self.token_budget_mock = MagicMock()
        
        # Set up return values for the mock classes
        self.redis_mock_class.return_value = self.redis_store_mock
        self.token_mock_class.return_value = self.token_budget_mock
        
        # Create a test Memory instance
        self.test_memory = Memory(
            memory_id="test123",
            content="Test memory content",
            metadata={"tag": "test"},
            importance=0.5,
            tier=MemoryTier.WORKING
        )
        
        # Create MemoryManager instance with test framework
        self.manager = MemoryManager(
            framework="test_framework"
        )
        
        # Set a test session ID
        self.test_session_id = "test_session"
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop the patches
        self.redis_patcher.stop()
        self.token_patcher.stop()
    
    def test_init(self):
        """Test initialization with different parameters."""
        # Test that RedisStore was initialized with the correct framework
        self.redis_mock_class.assert_called_with(
            redis_url="redis://localhost:6379/0",  # Note the /0 suffix
            expire_seconds=None,
            framework="test_framework"
        )
        
        # Test that TokenBudgetManager was initialized
        self.token_mock_class.assert_called_once()
        
        # Test framework was stored
        self.assertEqual(self.manager.framework, "test_framework")
        
        # Test default component_id is None
        self.assertIsNone(self.manager.component_id)
        
        # Test with custom Redis URL
        with patch('core.memory_manager.RedisStore') as redis_mock:
            manager = MemoryManager(redis_url="redis://custom:6380")
            redis_mock.assert_called_with(
                redis_url="redis://custom:6380",
                expire_seconds=None,
                framework="app"
            )
    
    def test_set_context(self):
        """Test setting component context and propagation to dependencies."""
        # Set context
        self.manager.set_context("test_component")
        
        # Check component ID was stored
        self.assertEqual(self.manager.component_id, "test_component")
        
        # Check context was propagated to dependencies
        self.redis_store_mock.set_context.assert_called_with("test_component")
        self.token_budget_mock.set_context.assert_called_with("test_component", None)
        
        # Test with session_id
        self.manager.set_context("new_component", "session123")
        self.assertEqual(self.manager.component_id, "new_component")
        self.token_budget_mock.set_context.assert_called_with("new_component", "session123")
    
    def test_add_memory(self):
        """Test adding a memory with proper tier handling and namespacing."""
        # Set up mock to return a memory ID
        memory_id = "new_memory_123"
        self.redis_store_mock.add.return_value = memory_id
        
        # Create a test scenario with both approaches
        test_cases = [
            # Case 1: Test environment (metadata preserved exactly)
            {'patch_test_env': True, 'expected_metadata': {"test": "value"}},
            # Case 2: Production environment (metadata enriched with session_id and type)
            {'patch_test_env': False, 'expected_metadata': {"test": "value", "session_id": "test_session", "type": "session_context"}},
        ]
        
        # Test both cases
        for case in test_cases:
            with patch.object(MemoryManager, '_is_test_environment', return_value=case['patch_test_env']):
                # Reset the mock for this test case
                self.redis_store_mock.add.reset_mock()
                
                # Add memory with enum tier
                result_id = self.manager.add_memory(
                    content="Test content",
                    metadata={"test": "value"},
                    importance=0.8,
                    tier=MemoryTier.WORKING,
                    session_id=self.test_session_id
                )
                
                # Verify ID was returned
                self.assertEqual(result_id, memory_id)
                
                # Verify store was called with correct parameters
                self.redis_store_mock.add.assert_called_once()
                
                # Extract arguments using call_args
                call_args = self.redis_store_mock.add.call_args[0]  # Positional args as tuple
                memory_arg = call_args[0]  # First arg (memory)
                session_id_arg = call_args[1]  # Second arg (session_id)
                
                # Verify memory object properties
                self.assertEqual(memory_arg.content, "Test content")
                self.assertEqual(memory_arg.metadata, case['expected_metadata'], 
                                f"Metadata doesn't match for test_env={case['patch_test_env']}")
                self.assertEqual(memory_arg.importance, 0.8)
                self.assertEqual(memory_arg.tier, MemoryTier.WORKING)
                
                # Verify session_id was passed correctly
                self.assertEqual(session_id_arg, self.test_session_id)
    
    def test_add_memory_with_component_context(self):
        """Test adding a memory with component context set."""
        # Set component context
        self.manager.set_context("test_component")
        
        # Set up mock to return a memory ID
        memory_id = "memory_with_component_123"
        self.redis_store_mock.add.return_value = memory_id
        self.redis_store_mock.add.reset_mock()
        
        # Patch the _is_test_environment method to return False
        # so component_id will be added to metadata
        with patch.object(MemoryManager, '_is_test_environment', return_value=False):
            # Add memory
            result_id = self.manager.add_memory(
                content="Test content",
                metadata={"test_key": "test_value"},
                tier=MemoryTier.WORKING,
                session_id=self.test_session_id
            )
            
            # Verify the returned memory ID
            self.assertEqual(result_id, memory_id)
            
            # Verify add was called once
            self.redis_store_mock.add.assert_called_once()
            
            # Verify component_id and other metadata was added
            call_args = self.redis_store_mock.add.call_args[0]  # Positional args as tuple
            memory_arg = call_args[0]  # First arg (memory)
            expected_metadata = {
                "test_key": "test_value", 
                "component_id": "test_component", 
                "session_id": "test_session", 
                "type": "session_context"
            }
            self.assertEqual(memory_arg.metadata, expected_metadata)
            
            # Verify session_id was passed correctly
            session_id_arg = call_args[1]  # Second arg (session_id)
            self.assertEqual(session_id_arg, self.test_session_id)
    
    def test_get_memory(self):
        """Test retrieving a memory with proper tier string conversion."""
        # Set up mock to return a memory
        self.redis_store_mock.get.return_value = self.test_memory
        
        # Get memory with enum tier
        memory = self.manager.get_memory(
            memory_id="test123",
            tier=MemoryTier.WORKING,
            session_id=self.test_session_id
        )
        
        # Verify memory was returned
        self.assertEqual(memory, self.test_memory)
        
        # Verify store was called with string tier
        self.redis_store_mock.get.assert_called_with(
            memory_id="test123",
            tier_str="working",
            session_id=self.test_session_id
        )
    
    def test_get_memory_string_tier(self):
        """Test retrieving a memory with string tier."""
        # Set up mock to return a memory
        self.redis_store_mock.get.return_value = self.test_memory
        
        # Get memory with string tier
        memory = self.manager.get_memory(
            memory_id="test123",
            tier="working",
            session_id=self.test_session_id
        )
        
        # Verify memory was returned
        self.assertEqual(memory, self.test_memory)
        
        # Verify store was called with same string tier
        self.redis_store_mock.get.assert_called_with(
            memory_id="test123",
            tier_str="working",
            session_id=self.test_session_id
        )
    
    def test_get_memory_unknown_tier(self):
        """Test retrieving a memory with unknown tier."""
        # Get memory with unknown tier string
        self.manager.get_memory(
            memory_id="test123",
            tier="unknown_tier",
            session_id=self.test_session_id
        )
        
        # Verify store was called with the tier string as is
        self.redis_store_mock.get.assert_called_with(
            memory_id="test123",
            tier_str="unknown_tier",
            session_id=self.test_session_id
        )
    
    def test_update_memory(self):
        """Test updating a memory with proper component context."""
        # Set component context
        self.manager.set_context("update_component")
        
        # Update memory
        self.manager.update_memory(
            self.test_memory,
            session_id=self.test_session_id
        )
        
        # Verify component_id was added to metadata
        self.redis_store_mock.update.assert_called_once()
        call_args = self.redis_store_mock.update.call_args[0]
        memory_arg = call_args[0]
        self.assertEqual(memory_arg.metadata.get("component_id"), "update_component")
        
        # Verify session_id was passed to store
        self.assertEqual(call_args[1], self.test_session_id)
    
    def test_delete_memory(self):
        """Test deleting a memory with proper tier string conversion."""
        # Delete memory with enum tier
        self.manager.delete_memory(
            memory_id="test123",
            tier=MemoryTier.SHORT_TERM,
            session_id=self.test_session_id
        )
        
        # Debug output
        print(f"\nActual calls to delete: {self.redis_store_mock.delete.call_args_list}")
        print(f"Expected: memory_id='test123', tier_str='short_term', session_id='{self.test_session_id}'\n")
        
        # Verify store was called with string tier
        self.redis_store_mock.delete.assert_called_with(
            memory_id="test123",
            tier_str="short_term",
            session_id=self.test_session_id
        )
    
    def test_list_memories(self):
        """Test listing memories with proper tier string conversion."""
        # Set up mock to return memories
        test_memories = [self.test_memory]
        self.redis_store_mock.list.return_value = test_memories
        
        # List memories with enum tier
        memories = self.manager.list_memories(
            tier=MemoryTier.WORKING,
            session_id=self.test_session_id,
            limit=10,
            offset=0
        )
        
        # Verify memories were returned
        self.assertEqual(memories, test_memories)
        
        # Verify store was called with string tier
        self.redis_store_mock.list.assert_called_with(
            tier_str="working",
            session_id=self.test_session_id,
            limit=10,
            offset=0
        )
    
    def test_search_by_metadata(self):
        """Test searching memories by metadata with tier conversion."""
        # Set up mock to return memories
        test_memories = [self.test_memory]
        
        # Reset the mock to ensure clean state
        self.redis_store_mock.search_by_metadata.reset_mock()
        self.redis_store_mock.search_by_metadata.return_value = test_memories
        
        # Search by metadata
        memories = self.manager.search_by_metadata(
            query={"tag": "important"},
            tier=MemoryTier.WORKING,
            limit=10
        )
        
        # Verify the returned memories
        self.assertEqual(memories, test_memories)
        
        # Verify the RedisStore.search_by_metadata was called with correct parameters
        self.redis_store_mock.search_by_metadata.assert_called_once_with(
            query={"tag": "important"}, 
            tier_str="working", 
            limit=10
        )
    
    def test_generate_prompt(self):
        """Test prompt generation with token budget manager integration."""
        # Reset and configure mocks
        self.token_budget_mock.construct_prompt_with_memories.reset_mock()
        
        # Define test data
        test_memory = Memory(
            memory_id="test_memory_1",
            content="Test memory content",
            metadata={"tag": "test"},
            importance=0.5,
            tier=MemoryTier.SHORT_TERM
        )
        
        short_term_memories = [test_memory]
        working_memories = []
        expected_prompt = ("Generated prompt with memories", {"tokens": 100})
        
        # Create patches with context manager to ensure proper cleanup
        with patch.object(MemoryManager, 'get_recent_turns') as mock_get_turns, \
             patch.object(MemoryManager, '_search_by_metadata_in_tier') as mock_search:
            
            # Configure return values for the patched methods
            mock_get_turns.return_value = short_term_memories
            mock_search.return_value = working_memories
            self.token_budget_mock.construct_prompt_with_memories.return_value = expected_prompt
            
            # Call the method being tested
            prompt, stats = self.manager.generate_prompt(
                session_id=self.test_session_id,
                user_query="Test query",
                system_message="System message",
                max_short_term_turns=10,
                include_working_memory=True
            )
            
            # Verify the results
            self.assertEqual(prompt, "Generated prompt with memories")
            self.assertEqual(stats, {"tokens": 100})
            
            # Verify the mocked method calls
            mock_get_turns.assert_called_once_with(
                self.test_session_id, n_turns=10
            )
            
            expected_query = {"session_id": self.test_session_id, "type": "session_context"}
            mock_search.assert_called_once_with(
                expected_query, MemoryTier.WORKING, limit=50
            )
            
            # Verify token budget manager call
            self.token_budget_mock.construct_prompt_with_memories.assert_called_once_with(
                system_message="System message",
                user_query="Test query",
                short_term_memories=short_term_memories,
                working_memories=working_memories,
                long_term_memories=[]
            )
    
    def test_get_tier_string(self):
        """Test tier string conversion with various input types."""
        # Test with enum
        tier_str = self.manager._get_tier_string(MemoryTier.WORKING)
        self.assertEqual(tier_str, "working")
        
        # Test with string
        tier_str = self.manager._get_tier_string("working")
        self.assertEqual(tier_str, "working")
        
        # Test with unknown string
        tier_str = self.manager._get_tier_string("custom_tier")
        self.assertEqual(tier_str, "custom_tier")
        
        # Test with None (should default to "working")
        tier_str = self.manager._get_tier_string(None)
        self.assertEqual(tier_str, "working")
        
        # Test with integer (should convert to string)
        tier_str = self.manager._get_tier_string(123)
        self.assertEqual(tier_str, "123")


if __name__ == "__main__":
    unittest.main()
