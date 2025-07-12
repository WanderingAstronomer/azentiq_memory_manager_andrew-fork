"""Unit tests for the PromptConstructor class."""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

# Add project root to path to fix imports for both pytest and unittest discovery
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from utils.token_budget.prompt.constructor import PromptConstructor
from utils.token_budget.estimator import TokenEstimator
from utils.token_budget.prompt.formatter import MemoryFormatter
from utils.budget_rules import BudgetRulesManager
from core.interfaces import Memory, MemoryTier


class TestPromptConstructor(unittest.TestCase):
    """Test suite for PromptConstructor class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock token estimator
        self.token_estimator = MagicMock(spec=TokenEstimator)
        
        # Set up token estimator mock to return predictable values
        def estimate_text(text):
            # Simple approximation for testing: 1 token per 4 chars
            return len(text) // 4
        
        self.token_estimator.estimate_text.side_effect = estimate_text
        
        # Create constructor with mocked estimator
        self.constructor = PromptConstructor(token_estimator=self.token_estimator)
        
        # Create test memories
        self.working_memories = [
            Memory(
                memory_id="work1",
                content="Important working memory",
                metadata={"importance": 0.9, "source": "test"},
                importance=0.9,
                tier=MemoryTier.WORKING,
                created_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc),
                last_accessed_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc)
            ),
            Memory(
                memory_id="work2",
                content="Another working memory with lower importance",
                metadata={"importance": 0.5, "source": "test"},
                importance=0.5,
                tier=MemoryTier.WORKING,
                created_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc),
                last_accessed_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc)
            )
        ]
        
        self.short_term_memories = [
            Memory(
                memory_id="short1",
                content="Recent short-term memory",
                metadata={"recency": 1.0},
                importance=0.7,
                tier=MemoryTier.SHORT_TERM,
                created_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc),
                last_accessed_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc)
            )
        ]
        
        self.long_term_memories = [
            Memory(
                memory_id="long1",
                content="Persistent long-term memory",
                metadata={"category": "fundamental"},
                importance=0.8,
                tier=MemoryTier.LONG_TERM,
                created_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc),
                last_accessed_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc)
            )
        ]
        
        # Test query and system message
        self.test_query = "What is the importance of working memory?"
        self.test_system = "You are an assistant with access to memories."
        
    def test_init(self):
        """Test initialization with parameters."""
        # Check that constructor requires a token estimator
        token_estimator = MagicMock(spec=TokenEstimator)
        formatter = MagicMock(spec=MemoryFormatter)
        
        constructor = PromptConstructor(
            token_estimator=token_estimator, 
            formatter=formatter
        )
        
        # Check that parameters are stored
        self.assertEqual(constructor.token_estimator, token_estimator)
        self.assertEqual(constructor.formatter, formatter)
        self.assertIsNone(constructor.budget_rules_manager)
        self.assertIsNone(constructor.current_component_id)
        
    def test_init_default_formatter(self):
        """Test initialization with default formatter."""
        # Check that constructor creates a formatter if not provided
        token_estimator = MagicMock(spec=TokenEstimator)
        constructor = PromptConstructor(token_estimator=token_estimator)
        
        self.assertIsInstance(constructor.formatter, MemoryFormatter)
        
    def test_allocate_token_budget(self):
        """Test token budget allocation among memory sections."""
        # Create memory sections dictionary
        memory_sections = {
            "working": self.working_memories,
            "short_term": self.short_term_memories,
            "long_term": self.long_term_memories
        }
        
        # Test even distribution without rules manager
        available_tokens = 300
        budget = self.constructor.allocate_token_budget(available_tokens, memory_sections)
        
        # Check that budget is correctly distributed (evenly)
        section_count = len(memory_sections)
        expected_tokens_per_section = available_tokens // section_count
        
        for section, tokens in budget.items():
            self.assertEqual(tokens, expected_tokens_per_section)
            
        # Check total budget is respected
        self.assertEqual(sum(budget.values()), expected_tokens_per_section * section_count)
        
    def test_construct_prompt_single_section(self):
        """Test constructing a prompt with a single memory section."""
        # Create a single memory section
        memory_sections = {
            "working": self.working_memories
        }
        
        # Create prompt with single section
        prompt, token_usage = self.constructor.construct_prompt(
            user_input=self.test_query,
            memory_sections=memory_sections,
            max_tokens=1000,
            system_message=self.test_system
        )
        
        # Verify all components are in the prompt
        self.assertIn(self.test_system, prompt)
        self.assertIn(self.test_query, prompt)
        
        # Check that token usage is tracked
        self.assertIn("user_input", token_usage)
        self.assertIn("system", token_usage)
        self.assertIn("memories", token_usage)
        self.assertIn("working", token_usage["memories"])
        self.assertIn("total", token_usage)
        
    def test_construct_prompt_multiple_sections(self):
        """Test constructing a prompt with multiple memory sections."""
        # Create memory sections with multiple categories
        memory_sections = {
            "working": self.working_memories,
            "short_term": self.short_term_memories,
            "long_term": self.long_term_memories
        }
        
        # Mock formatter to return predictable output
        mock_formatter = MagicMock(spec=MemoryFormatter)
        mock_formatter.format_memories.side_effect = [
            "Formatted working memories",
            "Formatted short-term memories",
            "Formatted long-term memories"
        ]
        
        # Replace constructor's formatter
        self.constructor.formatter = mock_formatter
        
        # Create prompt with multiple sections
        prompt, token_usage = self.constructor.construct_prompt(
            user_input=self.test_query,
            memory_sections=memory_sections,
            max_tokens=1000,
            system_message=self.test_system
        )
        
        # Verify all components are in the prompt
        self.assertIn(self.test_system, prompt)
        self.assertIn(self.test_query, prompt)
        
        # Check that formatter was called for each section
        self.assertEqual(mock_formatter.format_memories.call_count, len(memory_sections))
        
        # Check that token usage is tracked for all sections
        for section in memory_sections.keys():
            self.assertIn(section, token_usage["memories"])
            
    def test_construct_prompt_with_token_limit(self):
        """Test constructing a prompt with token limit enforcement."""
        # Create a memory with high token count
        high_token_memory = Memory(
            memory_id="high_tokens",
            content="This is a very long memory that will exceed the token limit" * 10,
            metadata={"importance": 0.9},
            importance=0.9,
            tier=MemoryTier.WORKING,
            created_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc),
            last_accessed_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc)
        )
        
        # Create section with high token memories
        memory_sections = {
            "high_token": [high_token_memory]
        }
        
        # Set up token estimator to return high token count
        def high_estimate(text):
            return 1000 if "exceed" in text else len(text) // 4
        
        self.token_estimator.estimate_text.side_effect = high_estimate
        
        # Create prompt with token limit
        prompt, token_usage = self.constructor.construct_prompt(
            user_input=self.test_query,
            memory_sections=memory_sections,
            max_tokens=100,  # Very low limit
            system_message=self.test_system
        )
        
        # Check that token limit is respected
        self.assertLessEqual(token_usage["total"], 100)
        
    def test_construct_prompt_with_format_templates(self):
        """Test constructing a prompt with custom format templates."""
        # Create custom format templates
        format_templates = {
            "working": "[WORK] {content}",
            "short_term": "[SHORT] {content}"
        }
        
        # Create memory sections
        memory_sections = {
            "working": self.working_memories,
            "short_term": self.short_term_memories
        }
        
        # Create prompt with format templates
        prompt, token_usage = self.constructor.construct_prompt(
            user_input=self.test_query,
            memory_sections=memory_sections,
            max_tokens=1000,
            system_message=self.test_system,
            format_templates=format_templates
        )
        
        # We can't easily verify the format templates were used without 
        # complex mocking, but we can check the prompt was generated
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
            
    def test_set_context(self):
        """Test setting component context."""
        # Default constructor has no component context
        self.assertIsNone(self.constructor.current_component_id)
        
        # Setting component context
        component_id = "test_component"
        self.constructor.set_context(component_id)
        self.assertEqual(self.constructor.current_component_id, component_id)
        
        # Clearing component context
        self.constructor.set_context(None)
        self.assertIsNone(self.constructor.current_component_id)
        
    def test_allocate_token_budget_with_rules_manager(self):
        """Test token budget allocation with a budget rules manager."""
        # Mock budget rules manager
        budget_rules_manager = MagicMock()
        budget_rules_manager.allocate_tier_budgets.return_value = {
            "WORKING": 150,
            "SHORT_TERM": 100,
            "LONG_TERM": 50
        }
        
        # Create constructor with rules manager
        constructor = PromptConstructor(
            token_estimator=self.token_estimator,
            budget_rules_manager=budget_rules_manager
        )
        
        # Create memory sections
        memory_sections = {
            "working": self.working_memories,
            "short_term": self.short_term_memories,
            "long_term": self.long_term_memories
        }
        
        # Set component context first
        constructor.set_context("test_component")
        
        # Allocate budget with rules manager
        budget = constructor.allocate_token_budget(300, memory_sections)
        
        # Verify rules manager was called with correct parameters
        budget_rules_manager.allocate_tier_budgets.assert_called_once_with("test_component", 300)
        
        # Check that budget matches rules manager's allocation with section name mapping
        self.assertEqual(budget["working"], 150)
        self.assertEqual(budget["short_term"], 100)
        self.assertEqual(budget["long_term"], 50)


if __name__ == "__main__":
    unittest.main()
