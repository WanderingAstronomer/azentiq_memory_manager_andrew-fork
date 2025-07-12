from typing import Protocol, Dict, List, Any, Optional, TypeVar, Generic, Union
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class MemoryTier(Enum):
    """Memory tiers with different characteristics and lifetimes."""
    SHORT_TERM = "short_term"    # Conversation turns, short-lived
    WORKING = "working"          # Session context, persists for the session
    LONG_TERM = "long_term"      # Persistent knowledge

class Memory:
    """Base memory object structure for v1.0 schema."""
    def __init__(self, 
                 memory_id: str,
                 content: str,
                 metadata: Dict[str, Any] = None,
                 tier: MemoryTier = MemoryTier.WORKING,
                 ttl: Optional[int] = None,
                 created_at: Optional[datetime] = None,
                 last_accessed_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 importance: float = 0.0):
        """
        Initialize a new Memory object.
        
        Args:
            memory_id: Unique identifier for the memory
            content: The actual memory content
            metadata: Additional metadata (type, session_id, etc.)
            tier: Memory tier (SHORT_TERM, WORKING, LONG_TERM)
            ttl: Time-to-live in seconds (None = no expiration)
            created_at: Creation timestamp
            last_accessed_at: Last access timestamp
            updated_at: Last update timestamp
            importance: Importance score (0.0-1.0)
        """
        self.memory_id = memory_id
        self.content = content
        self.metadata = metadata or {}
        self.tier = tier
        self.ttl = ttl
        self.created_at = created_at or datetime.now()
        self.last_accessed_at = last_accessed_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.importance = importance
        
        # Ensure required metadata fields exist
        if "session_id" not in self.metadata:
            self.metadata["session_id"] = "default"  # Default session
            
        if "type" not in self.metadata:
            self.metadata["type"] = "generic"  # Default type
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for storage."""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "metadata": self.metadata,
            "tier": self.tier.value,
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "importance": self.importance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create memory from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) \
            if isinstance(data["created_at"], str) else data["created_at"]
            
        last_accessed_at = datetime.fromisoformat(data["last_accessed_at"]) \
            if isinstance(data["last_accessed_at"], str) else data["last_accessed_at"]
            
        updated_at = None
        if "updated_at" in data:
            updated_at = datetime.fromisoformat(data["updated_at"]) \
                if isinstance(data["updated_at"], str) else data["updated_at"]
        
        # Handle tier conversion
        tier = data.get("tier", MemoryTier.WORKING.value)
        if isinstance(tier, str):
            try:
                tier = MemoryTier(tier)
            except ValueError:
                tier = MemoryTier.WORKING  # Default if invalid
                
        return cls(
            memory_id=data["memory_id"],
            content=data["content"],
            metadata=data["metadata"],
            tier=tier,
            ttl=data.get("ttl"),
            created_at=created_at,
            updated_at=updated_at,
            last_accessed_at=last_accessed_at,
            importance=data.get("importance", 0.0)
        )


class IMemoryStore(Protocol, Generic[T]):
    """Interface for memory storage providers."""
    
    def add(self, memory: Memory) -> None:
        """Add a memory to the store."""
        ...
        
    def get(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID."""
        ...
        
    def update(self, memory: Memory) -> None:
        """Update an existing memory."""
        ...
        
    def delete(self, memory_id: str) -> None:
        """Delete a memory by ID."""
        ...
        
    def list(self, limit: int = 100, offset: int = 0) -> List[Memory]:
        """List memories with pagination."""
        ...
        
    def search_by_metadata(self, query: Dict[str, Any], limit: int = 10) -> List[Memory]:
        """Search memories by metadata."""
        ...


class IVectorStore(Protocol):
    """Interface for vector storage providers."""
    
    def add(self, memory: Memory, embedding: List[float]) -> None:
        """Add a memory with its embedding to the vector store."""
        ...
        
    def search_by_similarity(self, query_embedding: List[float], limit: int = 10) -> List[Memory]:
        """Search memories by embedding similarity."""
        ...
        
    def delete(self, memory_id: str) -> None:
        """Delete a memory by ID."""
        ...
