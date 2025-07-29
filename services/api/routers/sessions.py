from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.memory_manager import MemoryManager
from services.schemas.session import (
    ConversationTurn,
    ConversationTurnResponse,
    ConversationHistory,
    PromptRequest,
    PromptResponse,
    SessionContextResponse
)
from services.dependencies.memory_manager import get_memory_manager

router = APIRouter()


@router.post("/{session_id}/turns", response_model=ConversationTurnResponse)
async def add_conversation_turn(
    turn: ConversationTurn,
    session_id: str = Path(..., description="Session ID"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Add a conversation turn to short-term memory"""
    memory_id = memory_manager.add_conversation_turn(
        session_id=session_id,
        content=turn.content,
        role=turn.role,
        importance=turn.importance
    )
    
    if not memory_id:
        raise HTTPException(status_code=500, detail="Failed to add conversation turn")
    
    # Get the memory to return proper metadata
    memory = memory_manager.get_memory(memory_id)
    
    return ConversationTurnResponse(
        memory_id=memory_id,
        content=turn.content,
        role=turn.role,
        importance=turn.importance,
        timestamp=datetime.fromisoformat(memory.metadata.get("timestamp")) if memory else datetime.now()
    )


@router.get("/{session_id}/turns", response_model=ConversationHistory)
async def get_recent_turns(
    session_id: str = Path(..., description="Session ID"),
    n_turns: int = Query(10, description="Number of turns to retrieve", ge=1, le=50),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get recent conversation turns for a session"""
    memories = memory_manager.get_recent_turns(session_id, n_turns=n_turns)
    
    turns = []
    for memory in memories:
        turn = ConversationTurnResponse(
            memory_id=memory.memory_id,
            content=memory.content,
            role=memory.metadata.get("role", "unknown"),
            importance=memory.importance,
            timestamp=datetime.fromisoformat(memory.metadata.get("timestamp", datetime.now().isoformat()))
        )
        turns.append(turn)
    
    return ConversationHistory(
        session_id=session_id,
        turns=turns,
        count=len(turns)
    )


@router.post("/{session_id}/prompt", response_model=PromptResponse)
async def generate_prompt(
    request: PromptRequest,
    session_id: str = Path(..., description="Session ID"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Generate a prompt with memory integration"""
    prompt, token_usage = memory_manager.generate_prompt(
        session_id=session_id,
        system_message=request.system_message,
        user_query=request.user_query,
        max_short_term_turns=request.max_short_term_turns,
        include_working_memory=request.include_working_memory
    )
    
    return PromptResponse(
        prompt=prompt,
        token_usage=token_usage
    )


@router.get("/{session_id}/context", response_model=SessionContextResponse)
async def get_session_context(
    session_id: str = Path(..., description="Session ID"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get all context key-value pairs for a session"""
    context = memory_manager.get_session_context(session_id)
    
    return SessionContextResponse(
        session_id=session_id,
        context=context
    )


@router.put("/{session_id}/context/{key}", response_model=Dict[str, Any])
async def set_context_value(
    value: Any,
    session_id: str = Path(..., description="Session ID"),
    key: str = Path(..., description="Context key"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Set a context value for a session"""
    memory_manager.set_context_value(session_id, key, value)
    
    return {"key": key, "value": value, "session_id": session_id}
