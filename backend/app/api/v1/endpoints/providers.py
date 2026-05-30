"""Multi-provider chat endpoints - the heart of the Multi-AI platform."""

import json
import time
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.providers import (
    CompareRequest,
    CompareResponse,
    CompareResult,
    ModelInfoResponse,
    MultiChatRequest,
    MultiChatResponse,
    ProviderInfo,
)
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.chat import Chat
from app.models.session import Session
from app.models.user import User
from app.services.llm_router import get_llm_router
from app.services.memory_service import get_memory_service
from app.services.providers.registry import list_models, list_providers
from app.utils.logger import get_logger
from app.utils.token_counter import count_tokens

logger = get_logger(__name__)
router = APIRouter()

SYSTEM_PROMPT = (
    "You are an intelligent AI assistant. Provide helpful, accurate, and "
    "concise responses. Be conversational but professional."
)


async def _get_rag_context(message: str, user_id) -> str:
    """Retrieve RAG context for the user's documents.

    Returns an empty string if no documents exist or retrieval fails.
    Filtered by user_id so users only see their own documents.
    """
    try:
        from app.services.rag_service import get_rag_service
        from app.services.cost_service import get_cost_service

        rag = get_rag_service()
        if not rag.has_documents:
            logger.debug("[RAG] No documents in vector store, skipping context")
            return ""

        raw_context = await rag.get_context_string(
            message,
            filter_metadata={"user_id": str(user_id)},
        )
        if not raw_context:
            # Fallback: no per-user match, try unfiltered (single-user local dev)
            raw_context = await rag.get_context_string(message)

        if not raw_context:
            return ""

        # Compress to stay within token budget
        cost = get_cost_service()
        return cost.compress_context(raw_context)
    except Exception as e:
        logger.warning(f"[RAG] context retrieval failed: {e}")
        return ""


@router.get("/providers", response_model=List[ProviderInfo])
async def get_providers():
    """List all available providers and their configuration status."""
    return list_providers()


@router.get("/models")
async def get_all_models():
    """Aggregated model registry across all providers.

    Returns a dict keyed by provider id, each containing its model list.
    Only includes providers (configured or not) so the frontend can show all.
    """
    from app.services.providers.registry import PROVIDER_REGISTRY

    result = {}
    for provider_id in PROVIDER_REGISTRY:
        result[provider_id] = list_models(provider_id)
    return result


@router.get("/providers/{provider_id}/models", response_model=List[ModelInfoResponse])
async def get_provider_models(provider_id: str):
    """List all models for a specific provider."""
    return list_models(provider_id)


@router.post("/chat/multi", response_model=MultiChatResponse)
async def multi_chat(
    request: MultiChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to any provider with smart routing and fallback."""
    llm_router = get_llm_router()

    # Resolve session
    session_id = request.session_id
    if not session_id:
        session = Session(user_id=current_user.id, title=request.message[:50])
        db.add(session)
        await db.flush()
        session_id = session.id

    # Build message context from memory
    memory = get_memory_service(str(session_id))
    history = await memory.get_context()

    # ---- RAG: inject document context if the user has uploaded docs ----
    rag_context = await _get_rag_context(request.message, current_user.id)

    system_content = SYSTEM_PROMPT
    if rag_context:
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Use the following document context to answer the user's question. "
            f"If the answer isn't in the context, say so and use your general knowledge.\n"
            f"---\n{rag_context}\n---"
        )

    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": request.message})

    # Save user message
    db.add(Chat(
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=request.message,
        tokens_used=count_tokens(request.message),
    ))

    # Route to provider (with fallback)
    response = await llm_router.chat(
        messages=messages,
        provider=request.provider,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        enable_fallback=request.enable_fallback,
    )

    # Save assistant message with provider metadata
    db.add(Chat(
        session_id=session_id,
        user_id=current_user.id,
        role="assistant",
        content=response.content,
        tokens_used=response.total_tokens,
        latency_ms=response.latency_ms,
        model=f"{response.provider}/{response.model}",
    ))

    # Update memory
    await memory.add_message("user", request.message)
    await memory.add_message("assistant", response.content)

    await db.flush()

    return MultiChatResponse(
        content=response.content,
        provider=response.provider,
        model=response.model,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        latency_ms=response.latency_ms,
        cost=response.cost,
        session_id=str(session_id),
    )


@router.post("/chat/multi/stream")
async def multi_chat_stream(
    request: MultiChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a response from any provider with fallback via SSE."""
    llm_router = get_llm_router()

    # Resolve or create the session
    session_id = request.session_id
    if session_id:
        # Verify ownership
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            session_id = None  # invalid -> create new

    if not session_id:
        session = Session(user_id=current_user.id, title=request.message[:50])
        db.add(session)
        await db.flush()
        session_id = session.id

    session_id_str = str(session_id)
    user_id = current_user.id

    # Load memory context
    memory = get_memory_service(session_id_str)
    history = await memory.get_context()

    # ---- RAG: inject document context if the user has uploaded docs ----
    rag_context = await _get_rag_context(request.message, user_id)

    system_content = SYSTEM_PROMPT
    if rag_context:
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Use the following document context to answer the user's question. "
            f"If the answer isn't in the context, say so and use your general knowledge.\n"
            f"---\n{rag_context}\n---"
        )

    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": request.message})

    # Persist the USER message now (within the request's db session)
    db.add(Chat(
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=request.message,
        tokens_used=count_tokens(request.message),
    ))
    await db.flush()
    await db.commit()

    async def event_generator():
        full_response = ""
        used_provider = request.provider or "auto"
        used_model = request.model or ""
        total_tokens = 0
        try:
            async for chunk in llm_router.chat_stream(
                messages=messages,
                provider=request.provider,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                enable_fallback=request.enable_fallback,
            ):
                # Always attach session_id so the frontend tracks the session
                chunk["session_id"] = session_id_str

                if chunk.get("meta"):
                    used_provider = chunk.get("provider", used_provider)
                    used_model = chunk.get("model", used_model)
                    yield f"data: {json.dumps(chunk)}\n\n"
                    continue

                if chunk.get("content"):
                    full_response += chunk["content"]
                yield f"data: {json.dumps(chunk)}\n\n"

                if chunk.get("done"):
                    used_provider = chunk.get("provider", used_provider)
                    used_model = chunk.get("model", used_model)

            total_tokens = count_tokens(full_response)

            # Persist the ASSISTANT message using a fresh DB session
            # (the request-scoped `db` may already be closed by now)
            from app.db.database import async_session_factory
            async with async_session_factory() as save_db:
                save_db.add(Chat(
                    session_id=session_id,
                    user_id=user_id,
                    role="assistant",
                    content=full_response,
                    tokens_used=total_tokens,
                    model=f"{used_provider}/{used_model}",
                ))
                await save_db.commit()

            # Update in-memory conversation context
            await memory.add_message("user", request.message)
            await memory.add_message("assistant", full_response)

        except Exception as e:
            logger.error("Multi-stream failed", error=str(e))
            yield f"data: {json.dumps({'error': str(e), 'done': True, 'session_id': session_id_str})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/compare", response_model=CompareResponse)
async def compare_chat(
    request: CompareRequest,
    current_user: User = Depends(get_current_user),
):
    """Compare mode - send one prompt to multiple providers simultaneously."""
    llm_router = get_llm_router()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message},
    ]

    results = await llm_router.compare(
        messages=messages,
        providers=request.providers,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    return CompareResponse(
        results=[CompareResult(**r) for r in results]
    )
