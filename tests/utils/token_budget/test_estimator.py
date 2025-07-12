"""Unit tests for the TokenEstimator class."""

import unittest
from unittest.mock import MagicMock
import re

import sys
import os

# Add project root to path to fix imports for both pytest and unittest discovery
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

# Import required modules
from utils.token_budget.estimator import TokenEstimator
from core.interfaces import Memory


class TestTokenEstimator(unittest.TestCase):
    """Test suite for TokenEstimator class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create default estimator with standard parameters
        self.estimator = TokenEstimator()
        
        # Create an estimator with custom parameters for testing configuration
        self.custom_estimator = TokenEstimator({
            'chars_per_token': 3.0,  # More conservative estimate
            'words_per_token': 0.5   # More conservative estimate
        })
        
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        self.assertEqual(self.estimator.chars_per_token, 4.0)
        self.assertEqual(self.estimator.words_per_token, 0.75)
        self.assertDictEqual(self.estimator.config, {})
        
    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        self.assertEqual(self.custom_estimator.chars_per_token, 3.0)
        self.assertEqual(self.custom_estimator.words_per_token, 0.5)
        self.assertDictEqual(self.custom_estimator.config, {
            'chars_per_token': 3.0,
            'words_per_token': 0.5
        })
        
    def test_estimate_text_empty(self):
        """Test token estimation for empty text."""
        self.assertEqual(self.estimator.estimate_text(""), 0)
        
    def test_estimate_text_short(self):
        """Test token estimation for short text."""
        # Short text with known characteristics for verification
        text = "Hello, world!"
        
        char_count = len(text)
        word_count = len(re.findall(r'\b\w+\b', text))
        
        # Calculate expected token count using the formula from the implementation
        char_estimate = char_count / self.estimator.chars_per_token
        word_estimate = word_count / self.estimator.words_per_token
        expected = int((char_estimate + word_estimate) / 2) + 1
        
        self.assertEqual(self.estimator.estimate_text(text), expected)
        
    def test_estimate_text_long(self):
        """Test token estimation for longer text."""
        # Longer text to verify scaling behavior
        text = "This is a longer text that contains multiple sentences. " \
               "It should have a higher token count than the short example. " \
               "The estimator should scale appropriately with the length of the input text."
        
        char_count = len(text)
        word_count = len(re.findall(r'\b\w+\b', text))
        
        # Calculate expected token count using the formula from the implementation
        char_estimate = char_count / self.estimator.chars_per_token
        word_estimate = word_count / self.estimator.words_per_token
        expected = int((char_estimate + word_estimate) / 2) + 1
        
        self.assertEqual(self.estimator.estimate_text(text), expected)
        
    def test_custom_vs_default_estimator(self):
        """Test that custom parameters affect the estimation differently than defaults."""
        text = "This is a sample text for testing different estimators."
        
        # Custom estimator should give higher (more conservative) estimates
        # because it uses lower chars_per_token and words_per_token values
        default_estimate = self.estimator.estimate_text(text)
        custom_estimate = self.custom_estimator.estimate_text(text)
        
        self.assertGreater(custom_estimate, default_estimate)
        
    def test_estimate_memory_empty(self):
        """Test token estimation for an empty memory object."""
        # Create a mock Memory object with empty content and metadata
        memory = MagicMock(spec=Memory)
        memory.content = ""
        memory.metadata = {}
        
        # Should return the overhead (5) for an empty memory
        self.assertEqual(self.estimator.estimate_memory(memory), 5)
        
    def test_estimate_memory_with_content(self):
        """Test token estimation for a memory with content."""
        memory = MagicMock(spec=Memory)
        memory.content = "This is a memory content."
        memory.metadata = {}
        
        content_tokens = self.estimator.estimate_text(memory.content)
        expected = content_tokens + 5  # content tokens + overhead
        
        self.assertEqual(self.estimator.estimate_memory(memory), expected)
        
    def test_estimate_memory_with_metadata(self):
        """Test token estimation for a memory with content and metadata."""
        memory = MagicMock(spec=Memory)
        memory.content = "This is a memory content."
        memory.metadata = {"key1": "value1", "key2": 123}
        
        content_tokens = self.estimator.estimate_text(memory.content)
        metadata_tokens = self.estimator.estimate_text(str(memory.metadata))
        expected = content_tokens + metadata_tokens + 5  # content + metadata + overhead
        
        self.assertEqual(self.estimator.estimate_memory(memory), expected)
        
    def test_estimate_memory_complex(self):
        """Test token estimation for a memory with complex content and metadata."""
        memory = MagicMock(spec=Memory)
        memory.content = "This is a complex memory with multiple sentences. " \
                         "It contains various information that needs to be tokenized."
        memory.metadata = {
            "source": "system",
            "priority": "high",
            "tags": ["important", "reference", "context"],
            "timestamp": "2023-07-11T15:30:00Z",
            "nested": {
                "level1": {
                    "level2": "nested value"
                }
            }
        }
        
        content_tokens = self.estimator.estimate_text(memory.content)
        metadata_tokens = self.estimator.estimate_text(str(memory.metadata))
        expected = content_tokens + metadata_tokens + 5
        
        self.assertEqual(self.estimator.estimate_memory(memory), expected)


if __name__ == "__main__":
    unittest.main()
