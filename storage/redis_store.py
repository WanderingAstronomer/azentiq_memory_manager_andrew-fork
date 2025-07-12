import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

import redis

from core.interfaces import IMemoryStore, Memory


class RedisStore(IMemoryStore):
    """Redis implementation of the memory store for session memory."""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379", 
                 prefix: str = "memory:",
                 expire_seconds: Optional[int] = None,
                 framework: str = "app"):
        """Initialize Redis store.
        
        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for all memories
            expire_seconds: TTL for memory entries (None = no expiration)
            framework: The framework using this store (app, langchain, langgraph)
        """
        self.client = redis.from_url(redis_url)
        self.prefix = prefix
        self.expire_seconds = expire_seconds
        self.framework = framework
        self.current_component_id = None
    
    def set_context(self, component_id: Optional[str] = None):
        """Set the current component context.
        
        Args:
            component_id: Current component ID
        """
        if component_id:
            self.current_component_id = component_id
    
    def _get_namespace(self, 
                       memory_id: str, 
                       tier_str: str, 
                       session_id: Optional[str] = None) -> str:
        """Create a namespaced key following the pattern:
        {tier}:{session_id}:{framework}:{component_id}:{memory_id}
        
        Args:
            memory_id: Unique memory identifier
            tier_str: String representation of memory tier
            session_id: Optional session identifier
            
        Returns:
            Namespaced key string
        """
        # Use default placeholders for missing values
        sess = session_id or "global"
        comp = self.current_component_id or "main"
        
        # Create namespace using the defined pattern
        return f"{tier_str}:{sess}:{self.framework}:{comp}:{memory_id}"
    
    def _get_key(self, memory_id: str, tier_str: str = None, session_id: Optional[str] = None) -> str:
        """Create Redis key from memory ID with proper namespacing.
        
        Args:
            memory_id: Unique memory identifier
            tier_str: String representation of memory tier (optional)
            session_id: Optional session identifier
            
        Returns:
            Fully qualified Redis key
        """
        if tier_str and memory_id:
            # If we have tier info, use full namespacing
            namespace = self._get_namespace(memory_id, tier_str, session_id)
            return f"{self.prefix}{namespace}"
        else:
            # Fallback to simple prefix + id for backward compatibility
            return f"{self.prefix}{memory_id}"
    
    def add(self, memory: Memory, session_id: Optional[str] = None, tier_str: Optional[str] = None) -> str:
        """Add a memory to Redis.
        
        Args:
            memory: Memory object to store
            session_id: Optional session identifier for namespacing
            tier_str: Optional tier string override
            
        Returns:
            memory_id: The ID of the created/stored memory
        """
        # Generate ID if not provided
        if not memory.memory_id:
            memory.memory_id = str(uuid.uuid4())
        
        # Get tier string representation from parameter or memory object
        if tier_str is None:
            tier_str = memory.tier.name.lower() if hasattr(memory.tier, "name") else str(memory.tier).lower()
        
        # Extract session ID from memory metadata if not explicitly provided
        if not session_id and memory.metadata and "session_id" in memory.metadata:
            session_id = memory.metadata["session_id"]
            
        # Create namespaced key
        key = self._get_key(memory.memory_id, tier_str, session_id)
        value = json.dumps(memory.to_dict())
        
        if self.expire_seconds is not None:
            self.client.setex(key, self.expire_seconds, value)
        else:
            self.client.set(key, value)
            
        # Return the memory ID
        return memory.memory_id
    
    def get(self, memory_id: str, tier_str: Optional[str] = None, 
             session_id: Optional[str] = None) -> Optional[Memory]:
        """Retrieve a memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            tier_str: Optional tier string for namespacing
            session_id: Optional session ID for namespacing
            
        Returns:
            Memory object if found, None otherwise
        """
        # Try with namespacing if tier info provided
        if tier_str:
            key = self._get_key(memory_id, tier_str, session_id)
            data = self.client.get(key)
        else:
            # Try legacy format first
            key = self._get_key(memory_id)
            data = self.client.get(key)
            
            # If not found, try common tiers
            if not data:
                for tier in ["short_term", "working", "long_term"]:
                    key = self._get_key(memory_id, tier, session_id)
                    data = self.client.get(key)
                    if data:
                        break
        
        if not data:
            return None
            
        try:
            memory_dict = json.loads(data)
            memory = Memory.from_dict(memory_dict)
            
            # Update last accessed timestamp
            memory.last_accessed_at = datetime.now()
            self.update(memory, session_id)
            
            return memory
        except Exception as e:
            print(f"Error deserializing memory: {e}")
            return None
    
    def update(self, memory: Memory, session_id: Optional[str] = None) -> None:
        """Update an existing memory.
        
        Args:
            memory: Memory object to update
            session_id: Optional session identifier for namespacing
        """
        # Get tier string
        tier_str = memory.tier.name.lower() if hasattr(memory.tier, "name") else str(memory.tier).lower()
        
        # Extract session ID from memory metadata if not explicitly provided
        if not session_id and memory.metadata and "session_id" in memory.metadata:
            session_id = memory.metadata["session_id"]
        
        key = self._get_key(memory.memory_id, tier_str, session_id)
        memory.last_accessed_at = datetime.now()
        value = json.dumps(memory.to_dict())
        
        if self.expire_seconds is not None:
            self.client.setex(key, self.expire_seconds, value)
        else:
            self.client.set(key, value)
    
    def delete(self, memory_id: str, tier_str: Optional[str] = None, 
               session_id: Optional[str] = None) -> None:
        """Delete a memory by ID.
        
        Args:
            memory_id: ID of the memory to delete
            tier_str: Optional tier string for namespacing
            session_id: Optional session ID for namespacing
        """
        if tier_str:
            # Delete specific tier namespace
            key = self._get_key(memory_id, tier_str, session_id)
            self.client.delete(key)
        else:
            # Try to delete from all possible tiers
            # First try legacy format
            legacy_key = self._get_key(memory_id)
            self.client.delete(legacy_key)
            
            # Then try standard tiers
            for tier in ["short_term", "working", "long_term"]:
                key = self._get_key(memory_id, tier, session_id)
                self.client.delete(key)
    
    def list(self, limit: int = 100, offset: int = 0, 
             tier_str: Optional[str] = None,
             session_id: Optional[str] = None) -> List[Memory]:
        """List memories with pagination.
        
        Args:
            limit: Maximum number of memories to return
            offset: Starting offset for pagination
            tier_str: Optional tier filter
            session_id: Optional session ID filter
            
        Returns:
            List of memory objects
        """
        # Create pattern based on filters
        if tier_str and session_id:
            # Full namespace pattern: tier:session:framework:component:*
            comp = self.current_component_id or "*"
            pattern = f"{self.prefix}{tier_str}:{session_id}:{self.framework}:{comp}:*"
        elif tier_str:
            # Match tier regardless of session
            pattern = f"{self.prefix}{tier_str}:*"
        elif session_id:
            # Match session across tiers
            pattern = f"{self.prefix}*:{session_id}:*"
        else:
            # Match all memories with our prefix
            pattern = f"{self.prefix}*"
        
        # Scan for matching keys
        cursor = 0
        all_keys = []
        
        while True:
            cursor, keys = self.client.scan(cursor=cursor, match=pattern, count=1000)
            all_keys.extend(keys)
            
            if cursor == 0:
                break
        
        # Apply pagination
        paginated_keys = all_keys[offset:offset+limit]
        memories = []
        
        # Get memories for these keys
        if paginated_keys:
            values = self.client.mget(paginated_keys)
            
            for data in values:
                if data:
                    try:
                        memory_dict = json.loads(data)
                        memory = Memory.from_dict(memory_dict)
                        memories.append(memory)
                    except Exception as e:
                        print(f"Error deserializing memory: {e}")
        
        return memories
    
    def search_by_metadata(self, query: Dict[str, Any], limit: int = 10,
                          tier_str: Optional[str] = None) -> List[Memory]:
        """Search memories by metadata.
        
        Args:
            query: Dictionary of metadata key-value pairs to match
            limit: Maximum number of memories to return
            tier_str: Optional tier to search within
            
        Returns:
            List of matching memory objects
        """
        # Extract session_id from query if present for more efficient filtering
        session_id = query.get("session_id") if query and "session_id" in query else None
        
        # Use namespaced listing for better efficiency
        all_memories = self.list(limit=10000, tier_str=tier_str, session_id=session_id)
        matched_memories = []
        
        for memory in all_memories:
            matches = True
            
            for key, value in query.items():
                if key not in memory.metadata or memory.metadata[key] != value:
                    matches = False
                    break
            
            if matches:
                matched_memories.append(memory)
                if len(matched_memories) >= limit:
                    break
        
        return matched_memories
