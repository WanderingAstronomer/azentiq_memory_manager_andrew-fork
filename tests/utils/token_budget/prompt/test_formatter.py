"""Unit tests for the MemoryFormatter class."""

import unittest
from unittest.mock import MagicMock
import sys
import os
from datetime import datetime, timezone

# Add project root to path to fix imports for both pytest and unittest discovery
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from utils.token_budget.prompt.formatter import MemoryFormatter
from core.interfaces import Memory, MemoryTier


class TestMemoryFormatter(unittest.TestCase):
    """Test suite for MemoryFormatter class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create default formatter
        self.formatter = MemoryFormatter()
        
        # Create a test memory for reuse
        self.test_memory = Memory(
            memory_id="test123",
            content="Test memory content",
            metadata={"source": "test", "importance": 0.8},
            importance=0.8,
            tier=MemoryTier.WORKING,
            created_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc),
            last_accessed_at=datetime(2023, 7, 11, 15, 30, 0, tzinfo=timezone.utc)
        )
        
    def test_init_default_template(self):
        """Test initialization with default template."""
        self.assertEqual(
            self.formatter.default_format_template,
            "Memory {index}:\n{content}\n\n"
        )
        
    def test_init_custom_template(self):
        """Test initialization with custom template."""
        custom_formatter = MemoryFormatter(
            default_format_template="Custom: {content}"
        )
        
        self.assertEqual(custom_formatter.default_format_template, "Custom: {content}")
        
    def test_format_memory_default(self):
        """Test formatting a single memory with default template."""
        result = self.formatter.format_memory(self.test_memory)
        expected = "Memory 1:\nTest memory content\n\n"
        self.assertEqual(result, expected)
        
    def test_format_memory_custom(self):
        """Test formatting a memory with custom template."""
        custom_template = "ID: {id}\nContent: {content}\nCreated: {created_at}"
        result = self.formatter.format_memory(
            self.test_memory, 
            format_template=custom_template
        )
        
        self.assertIn("ID: test123", result)
        self.assertIn("Content: Test memory content", result)
        self.assertIn("Created: 2023-07-11T15:30:00+00:00", result)
        
    def test_format_memory_custom_template(self):
        """Test formatting with custom memory template."""
        custom_template = "#{index}. {content} (Importance: {importance:.1f})"
        
        formatted = self.formatter.format_memory(self.test_memory, index=2, format_template=custom_template)
        expected = "#2. Test memory content (Importance: 0.8)"
        
        self.assertEqual(formatted, expected)
        
    def test_format_memory_with_component_metadata(self):
        """Test formatting memory with component context in metadata."""
        memory_with_component = Memory(
            memory_id="comp123",
            content="Component memory content",
            metadata={
                "source": "test",
                "component_id": "planner",
                "framework": "langchain"
            },
            importance=0.9,
            tier=MemoryTier.WORKING
        )
        
        # Create a template that uses metadata
        metadata_template = "Content: {content}\nComponent: {metadata_component_id}\nFramework: {metadata_framework}"
        formatted = self.formatter.format_memory(memory_with_component, format_template=metadata_template)
        
        # Check that metadata placeholders are replaced
        self.assertIn("Content: Component memory content", formatted)
        self.assertIn("Component: planner", formatted)
        self.assertIn("Framework: langchain", formatted)
        
    def test_format_memories_empty(self):
        """Test formatting an empty memory list."""
        formatted = self.formatter.format_memories([], section_title="Empty Section")
        expected = ""
        
        self.assertEqual(formatted, expected)
        
    def test_format_memories(self):
        """Test formatting multiple memories."""
        # Create another test memory
        second_memory = Memory(
            memory_id="test456",
            content="Second memory content",
            metadata={"source": "another_test"},
            importance=0.5,
            tier=MemoryTier.SHORT_TERM
        )
        
        memories = [self.test_memory, second_memory]
        
        formatted = self.formatter.format_memories(memories, section_title="Test Memories")
        
        # Check section title
        self.assertIn("Test Memories", formatted)
        
        # Check that both memories are included
        self.assertIn("Memory 1:", formatted)
        self.assertIn("Test memory content", formatted)
        self.assertIn("Memory 2:", formatted)
        self.assertIn("Second memory content", formatted)
        
    def test_format_memories_custom_format_template(self):
        """Test formatting memories with custom format template."""
        custom_template = "Item #{index}: {content}"
        
        formatted = self.formatter.format_memories(
            [self.test_memory], 
            format_template=custom_template,
            section_title="Custom Section"
        )
        
        # Check custom format
        self.assertIn("Custom Section", formatted)
        self.assertIn("Item #1: Test memory content", formatted)
        
    def test_format_memory_special_chars(self):
        """Test formatting a memory with special characters."""
        memory_with_special = Memory(
            memory_id="special123",
            content="Memory with *special* _markdown_ characters\nand newlines",
            metadata={"tag": "special<>chars", "value": "quotes \"test\""},
            importance=0.7,
            tier=MemoryTier.WORKING
        )
        
        formatted = self.formatter.format_memory(memory_with_special)
        
        # Check that content is preserved
        self.assertIn("Memory with *special* _markdown_ characters", formatted)
        self.assertIn("and newlines", formatted)
        
    def test_complex_nested_metadata(self):
        """Test formatting a memory with complex nested metadata."""
        memory_with_complex = Memory(
            memory_id="complex123",
            content="Complex metadata memory",
            metadata={
                "simple": "value",
                "nested": {
                    "level1": {
                        "level2": "deep value"
                    },
                    "array": [1, 2, 3]
                },
                "session_id": "test_session",
                "component_id": "test_component",
                "framework": "test_framework"
            },
            importance=0.6,
            tier=MemoryTier.WORKING
        )
        
        # Create a template that uses nested metadata
        metadata_template = "{content}\nSimple: {metadata_simple}\nSession: {metadata_session_id}\nComponent: {metadata_component_id}\nFramework: {metadata_framework}"
        
        formatted = self.formatter.format_memory(memory_with_complex, format_template=metadata_template)
        
        # Check that metadata placeholders are replaced
        self.assertIn("Complex metadata memory", formatted)
        self.assertIn("Simple: value", formatted)
        self.assertIn("Session: test_session", formatted)
        self.assertIn("Component: test_component", formatted)
        self.assertIn("Framework: test_framework", formatted)
        
    def test_format_memory_sections(self):
        """Test formatting multiple memory sections."""
        # Create test memories for multiple sections
        working_memory = Memory(
            memory_id="working1",
            content="Working memory content",
            metadata={"section": "working"},
            importance=0.8,
            tier=MemoryTier.WORKING
        )
        
        short_term_memory = Memory(
            memory_id="short1",
            content="Short-term memory content",
            metadata={"section": "short_term"},
            importance=0.6,
            tier=MemoryTier.SHORT_TERM
        )
        
        # Create memory sections
        memory_sections = {
            "working": [working_memory],
            "short_term": [short_term_memory]
        }
        
        # Format with default templates
        formatted = self.formatter.format_memory_sections(memory_sections)
        
        # Check that section names and content are included
        self.assertIn("WORKING", formatted)
        self.assertIn("SHORT_TERM", formatted)
        self.assertIn("Working memory content", formatted)
        self.assertIn("Short-term memory content", formatted)
        
    def test_format_memory_sections_with_custom_templates(self):
        """Test formatting memory sections with custom templates."""
        # Create test memories
        working_memory = Memory(
            memory_id="working1",
            content="Working memory content",
            metadata={"section": "working"},
            importance=0.8,
            tier=MemoryTier.WORKING
        )
        
        short_term_memory = Memory(
            memory_id="short1",
            content="Short-term memory content",
            metadata={"section": "short_term"},
            importance=0.6,
            tier=MemoryTier.SHORT_TERM
        )
        
        # Create memory sections
        memory_sections = {
            "working": [working_memory],
            "short_term": [short_term_memory]
        }
        
        # Create custom format templates
        format_templates = {
            "working": "[W{index}] {content}",
            "short_term": "[ST{index}] {content}"
        }
        
        # Format with custom templates and title format
        formatted = self.formatter.format_memory_sections(
            memory_sections,
            format_templates=format_templates,
            title_format="== {section_name} =="
        )
        
        # Check custom formatting
        self.assertIn("== WORKING ==", formatted)
        self.assertIn("== SHORT_TERM ==", formatted)
        self.assertIn("[W1] Working memory content", formatted)
        self.assertIn("[ST1] Short-term memory content", formatted)


if __name__ == "__main__":
    unittest.main()
