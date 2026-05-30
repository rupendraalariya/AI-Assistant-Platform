"""Chat schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Chat message request schema."""

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    use_rag: bool = False
    stream: bool = False
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""

    id: str
    session_id: str
    role: str
    content: str
    tokens_used: int
    latency_ms: Optional[int] = None
    model: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Chat history response schema."""

    session_id: str
    messages: List[ChatMessageResponse]
    total_messages: int
    total_tokens: int


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    content: str
    done: bool = False
    session_id: Optional[str] = None
    tokens_used: Optional[int] = None
