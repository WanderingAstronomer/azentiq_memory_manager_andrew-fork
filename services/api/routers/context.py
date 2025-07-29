from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from core.memory_manager import MemoryManager
from services.schemas.session import ContextCreate
from services.dependencies.memory_manager import get_memory_manager

router = APIRouter()


@router.post("", status_code=204)
async def set_context(
    context: ContextCreate,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Set the component context for memory operations"""
    try:
        memory_manager.set_context(
            component_id=context.component_id,
            session_id=context.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set context: {str(e)}")
    
    return None
