from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class MemoryTierEnum(str, Enum):
    """Enum for memory tiers in API requests/responses"""
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"


class MemoryBase(BaseModel):
    """Base schema for memory objects"""
    content: str = Field(..., description="Content of the memory")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the memory")
    tier: MemoryTierEnum = Field(default=MemoryTierEnum.WORKING, description="Memory tier")
    importance: float = Field(default=0.0, ge=0.0, le=1.0, description="Importance score (0.0-1.0)")
    ttl: Optional[int] = Field(default=None, description="Time-to-live in seconds (None = no expiration)")


class MemoryCreate(MemoryBase):
    """Schema for memory creation requests"""
    memory_id: Optional[str] = Field(default=None, description="Optional memory ID (will be generated if not provided)")
    session_id: Optional[str] = Field(default=None, description="Session ID for this memory")


class MemoryUpdate(BaseModel):
    """Schema for memory update requests"""
    content: Optional[str] = Field(default=None, description="New content for the memory")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata updates for the memory")
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="New importance score (0.0-1.0)")
    tier: Optional[MemoryTierEnum] = Field(default=None, description="New memory tier")
    ttl: Optional[int] = Field(default=None, description="New time-to-live in seconds")


class MemoryRead(MemoryBase):
    """Schema for memory responses"""
    memory_id: str = Field(..., description="Unique identifier for the memory")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_accessed_at: datetime = Field(..., description="Last access timestamp")


class MemoryList(BaseModel):
    """Schema for paginated memory list responses"""
    items: List[MemoryRead] = Field(..., description="List of memories")
    total: int = Field(..., description="Total number of memories matching the query")
    limit: int = Field(..., description="Maximum number of items per page")
    offset: int = Field(..., description="Pagination offset")


class MetadataQuery(BaseModel):
    """Schema for metadata search requests"""
    query: Dict[str, Any] = Field(..., description="Metadata key-value pairs to match")
    tier: Optional[MemoryTierEnum] = Field(default=None, description="Memory tier to search in")
    limit: int = Field(default=10, description="Maximum number of results to return")
