"""Memory formatting utilities for prompt construction."""

import logging
from typing import List, Dict, Any, Optional

from core.interfaces import Memory

logger = logging.getLogger(__name__)

class MemoryFormatter:
    """Formats memories for inclusion in prompts with configurable templates."""
    
    def __init__(self, default_format_template: Optional[str] = None):
        """Initialize the formatter with an optional default template.
        
        Args:
            default_format_template: Optional default template string with {placeholder} format
        """
        self.default_format_template = default_format_template or "Memory {index}:\n{content}\n\n"
    
    def format_memory(self, memory: Memory, index: int = 1, format_template: Optional[str] = None) -> str:
        """Format a single memory according to a template.
        
        Args:
            memory: Memory object to format
            index: Index number for the memory (for numbered lists)
            format_template: Optional template string with {placeholder} format
            
        Returns:
            Formatted memory string
        """
        # Use provided template or default
        template = format_template or self.default_format_template
        
        # Create basic placeholders
        placeholders = {
            "index": index,
            "id": memory.memory_id,
            "content": memory.content,
            "importance": memory.importance,
            "tier": memory.tier.name if hasattr(memory.tier, "name") else str(memory.tier)
        }
        
        # Add created/accessed times if available
        if memory.created_at:
            placeholders["created_at"] = memory.created_at.isoformat()
        if memory.last_accessed_at:
            placeholders["last_accessed_at"] = memory.last_accessed_at.isoformat()
        
        # Add metadata if available
        if memory.metadata:
            placeholders["metadata"] = str(memory.metadata)
            
            # Add specific metadata fields for direct access
            for key, value in memory.metadata.items():
                placeholders[f"metadata_{key}"] = value
        
        # Apply template
        try:
            return template.format(**placeholders)
        except KeyError as e:
            # Fall back to basic format if template has missing keys
            logger.warning(f"Memory format template missing key: {e}")
            basic_format = "Memory {index}:\n{content}\n\n"
            return basic_format.format(index=index, content=memory.content)
    
    def format_memories(self, 
                      memories: List[Memory], 
                      format_template: Optional[str] = None,
                      section_title: Optional[str] = None) -> str:
        """Format a list of memories for inclusion in a prompt.
        
        Args:
            memories: List of Memory objects to format
            format_template: Optional template string with {placeholder} format
            section_title: Optional section title to include before memories
            
        Returns:
            Formatted memory string for prompt inclusion
        """
        if not memories:
            return ""
        
        # Format each memory
        formatted_memories = []
        for i, memory in enumerate(memories):
            formatted_memory = self.format_memory(
                memory, index=i+1, format_template=format_template)
            formatted_memories.append(formatted_memory)
        
        # Combine all formatted memories
        result = "".join(formatted_memories)
        
        # Add section title if provided
        if section_title:
            result = f"{section_title}\n{result}"
            
        return result
    
    def format_memory_sections(self, 
                             memory_sections: Dict[str, List[Memory]], 
                             format_templates: Optional[Dict[str, str]] = None,
                             title_format: str = "--- {section_name} ---") -> str:
        """Format multiple sections of memories.
        
        Args:
            memory_sections: Dictionary of section name to memory list
            format_templates: Optional dict of section name to format template
            title_format: Format string for section titles
            
        Returns:
            Formatted memory sections
        """
        if not memory_sections:
            return ""
            
        formatted_sections = []
        
        for section_name, memories in memory_sections.items():
            # Skip empty sections
            if not memories:
                continue
                
            # Get section-specific template if available
            template = None
            if format_templates and section_name in format_templates:
                template = format_templates[section_name]
                
            # Create section title
            section_title = title_format.format(section_name=section_name.upper())
            
            # Format this section's memories
            formatted_section = self.format_memories(
                memories, 
                format_template=template,
                section_title=section_title
            )
            
            # Add to result if not empty
            if formatted_section:
                formatted_sections.append(formatted_section)
                
        # Join all sections with double newlines
        return "\n\n".join(formatted_sections)
