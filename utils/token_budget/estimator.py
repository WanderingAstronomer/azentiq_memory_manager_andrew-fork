"""Token estimation utilities for memory management."""

import re
from typing import Dict, Any, Optional
from core.interfaces import Memory

class TokenEstimator:
    """Estimates token usage for text and memory objects.
    
    This class provides methods to estimate token counts for both raw text strings
    and Memory objects including metadata. It uses a simple approximation based on
    character and word counts, which can be replaced with more accurate model-specific
    tokenizers in production environments.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration.
        
        Args:
            config: Optional configuration dict with estimation parameters
        """
        self.config = config or {}
        
        # Default estimation parameters (can be overridden by config)
        # These are approximate values - in production, use model-specific tokenizers
        self.chars_per_token = self.config.get('chars_per_token', 4.0)
        self.words_per_token = self.config.get('words_per_token', 0.75)
        
    def estimate_text(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        
        This uses a simple approximation based on word count and character count.
        For production use, consider using a model-specific tokenizer.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
            
        # Simple estimation based on character and word count
        char_count = len(text)
        word_count = len(re.findall(r'\b\w+\b', text))
        
        # Average of character-based and word-based estimates
        char_estimate = char_count / self.chars_per_token
        word_estimate = word_count / self.words_per_token
        
        # Return average of the two estimates, rounded up to be conservative
        return int((char_estimate + word_estimate) / 2) + 1
        
    def estimate_memory(self, memory: Memory) -> int:
        """Estimate tokens for a memory object including content and metadata.
        
        Args:
            memory: Memory object
            
        Returns:
            Estimated token count
        """
        # Estimate content tokens
        content_tokens = self.estimate_text(memory.content)
        
        # Estimate metadata tokens (if any)
        metadata_tokens = 0
        if memory.metadata:
            # Convert metadata to string representation
            metadata_str = str(memory.metadata)
            metadata_tokens = self.estimate_text(metadata_str)
        
        # Add a small overhead for memory structure
        overhead = 5  # Token overhead for memory object structure
        
        return content_tokens + metadata_tokens + overhead
