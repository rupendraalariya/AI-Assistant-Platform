"""Multi-provider chat schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class MultiChatRequest(BaseModel):
    """Multi-provider chat request."""

    message: str = Field(..., min_length=1, max_length=20000)
    provider: Optional[str] = Field(
        default="auto",
        description="Provider id (openai, gemini, claude, groq, deepseek, mistral, together, ollama) or 'auto' for smart routing",
    )
    model: Optional[str] = Field(default=None, description="Model id; uses provider default if omitted")
    session_id: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=8000)
    enable_fallback: bool = True
    use_rag: bool = False


class MultiChatResponse(BaseModel):
    """Multi-provider chat response."""

    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    cost: float = 0.0
    session_id: Optional[str] = None


class ProviderInfo(BaseModel):
    """Provider metadata."""

    id: str
    name: str
    configured: bool
    requires_key: bool
    model_count: int


class ModelInfoResponse(BaseModel):
    """Model metadata."""

    id: str
    name: str
    context_window: int
    input_cost: float
    output_cost: float
    supports_streaming: bool


class CompareRequest(BaseModel):
    """Compare mode request - one prompt to many providers."""

    message: str = Field(..., min_length=1, max_length=20000)
    providers: List[dict] = Field(
        ...,
        description="List of {provider, model} specs",
        examples=[[
            {"provider": "openai", "model": "gpt-4o-mini"},
            {"provider": "claude", "model": "claude-3-5-sonnet-20241022"},
            {"provider": "gemini", "model": "gemini-2.0-flash"},
            {"provider": "deepseek", "model": "deepseek-chat"},
        ]],
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=8000)


class CompareResult(BaseModel):
    """A single provider's result in compare mode."""

    provider: str
    model: str
    content: str
    error: bool = False
    total_tokens: int = 0
    latency_ms: int = 0
    cost: float = 0.0


class CompareResponse(BaseModel):
    """Compare mode response."""

    results: List[CompareResult]
