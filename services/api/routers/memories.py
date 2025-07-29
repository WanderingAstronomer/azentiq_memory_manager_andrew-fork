from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os
import sys

# Import the pythonpath helper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.pythonpath_helper import add_project_root_to_path

# Add project root to path
project_root = add_project_root_to_path()
print(f"Added project root in memories.py: {project_root}")
print(f"Current sys.path: {sys.path}")

# Import core modules
from core.memory_manager import MemoryManager
from core.interfaces import MemoryTier, Memory
from storage.redis_store import RedisStore
from services.schemas.memory import (
    MemoryCreate,
    MemoryUpdate,
    MemoryRead,
    MemoryList,
    MetadataQuery,
    MemoryTierEnum
)
from services.dependencies.memory_manager import get_memory_manager

router = APIRouter()


def _convert_tier(tier: Optional[MemoryTierEnum]) -> Optional[MemoryTier]:
    """Convert API enum to core enum"""
    if tier is None:
        return None
    return MemoryTier(tier.value)


def _memory_to_read_model(memory) -> MemoryRead:
    """Convert core Memory to API MemoryRead model"""
    return MemoryRead(
        memory_id=memory.memory_id,
        content=memory.content,
        metadata=memory.metadata,
        tier=MemoryTierEnum(memory.tier.value),
        importance=memory.importance,
        ttl=memory.ttl,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        last_accessed_at=memory.last_accessed_at
    )


@router.post("", response_model=MemoryRead, status_code=201)
async def create_memory(
    memory: MemoryCreate,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Create a new memory"""
    tier = _convert_tier(memory.tier)
    
    # Extract optional session_id from the request if provided
    session_id = memory.session_id
    
    # Debug output
    print(f"DEBUG: Creating memory with tier={tier}, session_id={session_id}")
    print(f"DEBUG: Memory manager using redis_store at {memory_manager.redis_store.client}")
    
    # Remove session_id from metadata if it exists to avoid duplication
    metadata = memory.metadata.copy() if memory.metadata else {}
    if "session_id" not in metadata and session_id:
        metadata["session_id"] = session_id
    
    # Call memory manager to add the memory
    print(f"DEBUG: Adding memory with content={memory.content[:30]}..., metadata={metadata}")
    memory_id = memory_manager.add_memory(
        content=memory.content,
        metadata=metadata,
        importance=memory.importance,
        memory_id=memory.memory_id,
        tier=tier,
        session_id=session_id
    )
    print(f"DEBUG: Memory created with ID: {memory_id}")
    
    # Instead of trying to retrieve the memory through the MemoryManager,
    # create a Memory object directly from the data we just submitted
    from core.interfaces import Memory
    created_at = datetime.now()
    memory_obj = Memory(
        memory_id=memory_id,
        content=memory.content,
        metadata=metadata,
        importance=memory.importance,
        tier=tier,
        created_at=created_at,
        updated_at=created_at,
        last_accessed_at=created_at
    )
    
    # Return the memory model directly from our data
    return _memory_to_read_model(memory_obj)


@router.get("/{memory_id}", response_model=MemoryRead)
async def read_memory(
    memory_id: str = Path(..., description="Memory ID to retrieve"),
    tier: Optional[MemoryTierEnum] = Query(None, description="Memory tier to search in"),
    session_id: Optional[str] = Query(None, description="Session ID filter"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get a memory by ID"""
    import json  # Add import for direct Redis access
    from core.interfaces import Memory
    
    converted_tier = _convert_tier(tier)
    
    # Add debug logging
    print(f"DEBUG: Retrieving memory with ID={memory_id}, tier={converted_tier}, session_id={session_id}")
    print(f"DEBUG: Memory manager using redis_store at {memory_manager.redis_store.client}")
    
    try:
        # Try the direct method first with the provided parameters
        memory = None
        
        # Try with default session if none provided
        session_ids_to_try = [session_id] if session_id else [None, "default"]
        
        # Try different session IDs
        for sess_id in session_ids_to_try:
            print(f"DEBUG: Trying with session_id={sess_id}")
            
            # Try with specified tier if provided
            if converted_tier:
                memory = memory_manager.get_memory(memory_id, converted_tier, sess_id)
                if memory:
                    print(f"DEBUG: Found memory in tier {converted_tier} with session_id={sess_id}")
                    return _memory_to_read_model(memory)
            
            # Try tier-less lookup (tries all tiers internally)
            memory = memory_manager.get_memory(memory_id, None, sess_id)
            if memory:
                print(f"DEBUG: Found memory with tier-less lookup and session_id={sess_id}")
                return _memory_to_read_model(memory)
            
            # Explicit tier fallbacks
            for fallback_tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM]:
                memory = memory_manager.get_memory(memory_id, fallback_tier, sess_id)
                if memory:
                    print(f"DEBUG: Found memory in tier {fallback_tier} with session_id={sess_id}")
                    return _memory_to_read_model(memory)
        
        # Last resort: Try to access Redis directly using our memory ID
        print(f"DEBUG: Direct Redis lookup for memory ID {memory_id}")
        # We need to access the underlying Redis store
        redis_store = memory_manager.redis_store
        
        # Try using pattern matching to find our key
        cursor = 0
        pattern = f"*{memory_id}"
        found_keys = []
        
        while True:
            cursor, keys = redis_store.client.scan(cursor=cursor, match=pattern, count=100)
            found_keys.extend(keys)
            if cursor == 0:
                break
        
        if found_keys:
            print(f"DEBUG: Found {len(found_keys)} potential keys: {found_keys}")
            # Try to get the memory using the first key we found
            for key in found_keys:
                try:
                    data = redis_store.client.get(key)
                    if data:
                        memory_dict = json.loads(data)
                        memory = Memory.from_dict(memory_dict)
                        print(f"DEBUG: Successfully retrieved memory using key {key}")
                        return _memory_to_read_model(memory)
                except Exception as e:
                    print(f"DEBUG: Error with direct Redis access: {str(e)}")
        
        # If we reach here, the memory was not found
        print(f"DEBUG: Memory {memory_id} not found in any tier or session")
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        
    except Exception as e:
        print(f"DEBUG: Error retrieving memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving memory: {str(e)}")

    


@router.put("/{memory_id}", response_model=MemoryRead)
async def update_memory(
    update_data: MemoryUpdate,
    memory_id: str = Path(..., description="Memory ID to update"),
    session_id: Optional[str] = Query(None, description="Session ID filter"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Update an existing memory"""
    # Using a simplified approach - directly create/replace the memory
    
    # Debug logging
    update_tier = _convert_tier(update_data.tier) if update_data.tier else None
    print(f"DEBUG: Simplified update approach for memory ID={memory_id}, tier={update_tier}")
    
    try:
        # We'll use a two-step process:
        # 1. Try to retrieve existing memory to preserve attributes not in update request
        # 2. Create a new memory with the same ID using add_memory (which will overwrite)
        
        existing_memory = None
        
        # Try to find the existing memory to get its current attributes
        session_ids_to_try = [session_id] if session_id else [None, "default"]
        tiers_to_try = [update_tier] if update_tier else [None, MemoryTier.WORKING, MemoryTier.SHORT_TERM]
        
        for sess_id in session_ids_to_try:
            for tier in tiers_to_try:
                try:
                    memory = memory_manager.get_memory(memory_id, tier, sess_id)
                    if memory:
                        print(f"DEBUG: Found existing memory in tier={tier}, session={sess_id}")
                        existing_memory = memory
                        break
                except Exception as e:
                    print(f"DEBUG: Error checking tier {tier}, session {sess_id}: {str(e)}")
            if existing_memory:
                break
                
        # Prepare memory attributes for update
        content = update_data.content
        metadata = update_data.metadata or {}
        importance = update_data.importance
        tier = update_tier or MemoryTier.WORKING  # Default to working tier if not specified
        
        # If we found existing memory, use its values for any missing fields
        if existing_memory:
            if content is None:
                content = existing_memory.content
                
            if metadata is None:
                metadata = existing_memory.metadata
            elif existing_memory.metadata:
                # Merge metadata instead of replacing
                merged_metadata = dict(existing_memory.metadata)  # Create copy
                merged_metadata.update(metadata)  # Update with new values
                metadata = merged_metadata
                
            if importance is None:
                importance = existing_memory.importance
                
            if update_tier is None:
                tier = existing_memory.tier
        
        # Add the updated memory (this will overwrite any existing memory with same ID)
        print(f"DEBUG: Creating/updating memory with ID={memory_id}, content={content[:30]}..., tier={tier}")
        
        # Use add_memory to create/overwrite the memory
        result = memory_manager.add_memory(
            content=content,
            metadata=metadata,
            importance=importance,
            tier=tier,
            memory_id=memory_id,  # Use the specified ID to overwrite
            session_id="default"  # Always use default session for API
        )
        
        if not result:
            print(f"DEBUG: Failed to update memory {memory_id}")
            raise HTTPException(status_code=500, detail="Failed to update memory")
            
        print(f"DEBUG: Successfully updated memory {memory_id}")
        
        # Check if the result is a Memory object or just a string (memory_id)
        if isinstance(result, str):
            print(f"DEBUG: add_memory returned string ID: {result}")
            # Since we have the memory attributes, construct a Memory object manually
            updated_memory = Memory(
                memory_id=result,
                content=content,
                metadata=metadata,
                importance=importance,
                tier=tier,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        else:
            updated_memory = result
            
        return _memory_to_read_model(updated_memory)
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: Error in update_memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating memory: {str(e)}")



@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str = Path(..., description="Memory ID to delete"),
    tier: Optional[MemoryTierEnum] = Query(None, description="Memory tier to delete from"),
    session_id: Optional[str] = Query(None, description="Session ID filter"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Delete a memory"""
    # Debug logging
    converted_tier = _convert_tier(tier) if tier else None
    print(f"DEBUG: Deleting memory with ID={memory_id}, tier={converted_tier}, session_id={session_id}")
    
    try:
        # First try with the specified tier
        if converted_tier:
            success = memory_manager.delete_memory(memory_id, converted_tier, session_id)
            if success:
                print(f"DEBUG: Successfully deleted memory from tier {converted_tier}")
                return None
        
        # If not found or no tier specified, try all tiers
        print(f"DEBUG: Trying to delete from all tiers")
        for tier_to_try in [MemoryTier.WORKING, MemoryTier.SHORT_TERM]:
            success = memory_manager.delete_memory(memory_id, tier_to_try, session_id)
            if success:
                print(f"DEBUG: Successfully deleted memory from tier {tier_to_try}")
                return None
        
        # If we reached here, memory was not found in any tier
        print(f"DEBUG: Memory {memory_id} not found in any tier for deletion")
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        
    except Exception as e:
        print(f"DEBUG: Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting memory: {str(e)}")


@router.get("", response_model=MemoryList)
async def list_memories(
    tier: Optional[MemoryTierEnum] = Query(None, description="Memory tier to filter by"),
    session_id: Optional[str] = Query(None, description="Session ID to filter by"),
    limit: int = Query(100, description="Maximum number of memories to return", ge=1, le=1000),
    offset: int = Query(0, description="Pagination offset", ge=0),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """List memories with pagination and optional filtering"""
    memories = memory_manager.list_memories(
        tier=_convert_tier(tier) if tier else None,
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    # For a proper paginated response, we should also get the total count
    # This is a simplified version
    total = len(memories)  # In a real implementation, you would get the actual total count
    
    return MemoryList(
        items=[_memory_to_read_model(mem) for mem in memories],
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/search", response_model=List[MemoryRead])
async def search_memories(
    query: MetadataQuery,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Search memories by metadata"""
    memories = memory_manager.search_by_metadata(
        query=query.query,
        tier=_convert_tier(query.tier) if query.tier else None,
        limit=query.limit
    )
    
    return [_memory_to_read_model(mem) for mem in memories]
