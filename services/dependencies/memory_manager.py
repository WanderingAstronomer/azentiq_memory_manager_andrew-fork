from fastapi import Depends
from typing import Optional
from functools import lru_cache
import os
import sys

# Add project root to Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    print(f"Added {root_dir} to Python path in memory_manager.py")

from core.memory_manager import MemoryManager

@lru_cache()
def get_memory_manager_instance() -> MemoryManager:
    """
    Create or get a cached MemoryManager instance.
    
    This function ensures we have a single instance of MemoryManager
    throughout the application lifecycle.
    """
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    short_term_ttl = int(os.environ.get("SHORT_TERM_TTL", 30 * 60))  # 30 minutes default
    model_token_limit = int(os.environ.get("MODEL_TOKEN_LIMIT", 8192))
    
    # Create the memory manager instance
    memory_manager = MemoryManager(
        redis_url=redis_url,
        short_term_ttl=short_term_ttl,
        model_token_limit=model_token_limit,
        framework="api"  # Set framework to identify memories created by API
    )
    
    # Set consistent context for all operations
    memory_manager.set_context("main", "default")
    
    return memory_manager

def get_memory_manager() -> MemoryManager:
    """
    FastAPI dependency that provides the MemoryManager instance.
    
    This can be extended to include authentication and authorization checks
    before returning the MemoryManager instance.
    """
    return get_memory_manager_instance()
