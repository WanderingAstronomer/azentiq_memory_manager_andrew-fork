from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime


class ContextValue(BaseModel):
    """Schema for a single context key-value pair"""
    key: str = Field(..., description="Context key")
    value: Any = Field(..., description="Context value")


class ContextCreate(BaseModel):
    """Schema for setting context"""
    component_id: str = Field(..., description="Component identifier")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")


class SetContextValue(BaseModel):
    """Schema for setting a single context value"""
    value: Any = Field(..., description="Context value to store")
    ttl: Optional[int] = Field(default=None, description="Optional TTL in seconds")


class SessionContextResponse(BaseModel):
    """Schema for session context response"""
    session_id: str = Field(..., description="Session identifier")
    context: Dict[str, Any] = Field(..., description="All context key-value pairs for the session")


class ConversationTurn(BaseModel):
    """Schema for a conversation turn"""
    content: str = Field(..., description="Content of the message")
    role: str = Field(..., description="Role of the speaker (e.g., 'user', 'assistant')")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0.0-1.0)")


class ConversationTurnResponse(ConversationTurn):
    """Schema for conversation turn response"""
    memory_id: str = Field(..., description="Memory ID of the stored turn")
    timestamp: datetime = Field(..., description="Timestamp when the turn was added")


class ConversationHistory(BaseModel):
    """Schema for conversation history response"""
    session_id: str = Field(..., description="Session identifier")
    turns: List[ConversationTurnResponse] = Field(..., description="List of conversation turns")
    count: int = Field(..., description="Total number of turns")


class PromptRequest(BaseModel):
    """Schema for prompt generation request"""
    system_message: str = Field(..., description="System instructions/prompt")
    user_query: str = Field(..., description="The user's current query")
    max_short_term_turns: int = Field(default=10, description="Maximum number of conversation turns to consider")
    include_working_memory: bool = Field(default=True, description="Whether to include working memory items")


class PromptResponse(BaseModel):
    """Schema for prompt generation response"""
    prompt: str = Field(..., description="Constructed prompt with memories")
    token_usage: Dict[str, int] = Field(..., description="Token usage statistics")
