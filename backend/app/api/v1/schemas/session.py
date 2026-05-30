"""Session schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """Create session request schema."""

    title: Optional[str] = Field(None, max_length=255)
    model: str = Field(default="gpt-4o-mini")


class SessionResponse(BaseModel):
    """Session response schema."""

    id: str
    title: str
    model: str
    total_tokens: int
    total_cost: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """List of sessions response."""

    sessions: List[SessionResponse]
    total: int
