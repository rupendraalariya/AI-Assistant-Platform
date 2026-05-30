"""Chat endpoints - message handling and streaming."""

import json
import time
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.chat import Chat
from app.models.session import Session
from app.models.user import User
from app.services.llm_service import get_llm_service
from app.services.memory_service import get_memory_service
from app.services.rag_service import get_rag_service
from app.services.cost_service import get_cost_service
from app.utils.logger import get_logger
from app.utils.token_counter import count_tokens

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and receive a response."""
    start_time = time.time()

    # Get or create session
    session_id = request.session_id
    if not session_id:
        session = Session(
            user_id=current_user.id,
            title=request.message[:50],
        )
        db.add(session)
        await db.flush()
        session_id = session.id
    else:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Session", str(session_id))

    # Save user message to DB
    user_chat = Chat(
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=request.message,
        tokens_used=count_tokens(request.message),
    )
    db.add(user_chat)

    # Load memory context (never crashes - uses fallback)
    memory = get_memory_service(str(session_id))
    chat_history = await memory.get_context()

    # Get RAG context if requested
    context = None
    if request.use_rag:
        try:
            rag_service = get_rag_service()
            if rag_service.has_documents:
                cost_service = get_cost_service()
                raw_context = await rag_service.get_context_string(request.message)
                context = cost_service.compress_context(raw_context)
        except Exception as e:
            logger.warning("RAG retrieval failed, continuing without context", error=str(e))

    # Generate LLM response
    llm_service = get_llm_service(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    try:
        result = await llm_service.generate_response(
            user_message=request.message,
            chat_history=chat_history,
            context=context,
        )
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg or "429" in error_msg:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="OpenAI API quota exceeded. Please check your billing at platform.openai.com"
            )
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="OpenAI API key is invalid or missing. Check your .env configuration."
            )
        raise

    latency_ms = int((time.time() - start_time) * 1000)

    # Save assistant message to DB
    assistant_chat = Chat(
        session_id=session_id,
        user_id=current_user.id,
        role="assistant",
        content=result["content"],
        tokens_used=result["tokens_used"],
        latency_ms=latency_ms,
        model=result["model"],
    )
    db.add(assistant_chat)

    # Update memory (fire-and-forget, never blocks response)
    await memory.add_message("user", request.message)
    await memory.add_message("assistant", result["content"])

    # Check if summarization needed (non-blocking)
    try:
        if await memory.should_summarize():
            all_messages = await memory.get_all_messages()
            if all_messages:
                summary = await llm_service.summarize_conversation(all_messages)
                await memory.save_summary(summary)
    except Exception as e:
        logger.warning("Summarization skipped", error=str(e))

    await db.flush()

    return ChatMessageResponse(
        id=assistant_chat.id,
        session_id=session_id,
        role="assistant",
        content=result["content"],
        tokens_used=result["tokens_used"],
        latency_ms=latency_ms,
        model=result["model"],
        created_at=assistant_chat.created_at,
    )


@router.post("/stream")
async def stream_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and receive a streaming response via SSE."""

    # Get or create session
    session_id = request.session_id
    if not session_id:
        session = Session(
            user_id=current_user.id,
            title=request.message[:50],
        )
        db.add(session)
        await db.flush()
        session_id = session.id

    # Load memory context (never crashes)
    memory = get_memory_service(str(session_id))
    chat_history = await memory.get_context()

    # Get RAG context if requested
    context = None
    if request.use_rag:
        try:
            rag_service = get_rag_service()
            if rag_service.has_documents:
                context = await rag_service.get_context_string(request.message)
        except Exception:
            pass

    # Generate streaming response
    llm_service = get_llm_service(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    async def event_generator():
        full_response = ""
        try:
            async for token in llm_service.generate_stream(
                user_message=request.message,
                chat_history=chat_history,
                context=context,
            ):
                full_response += token
                data = json.dumps({"content": token, "done": False})
                yield f"data: {data}\n\n"

            # Final event with metadata
            tokens_used = count_tokens(full_response)
            data = json.dumps({
                "content": "",
                "done": True,
                "session_id": str(session_id),
                "tokens_used": tokens_used,
            })
            yield f"data: {data}\n\n"

            # Save to memory (non-blocking, never crashes the stream)
            try:
                await memory.add_message("user", request.message)
                await memory.add_message("assistant", full_response)
            except Exception:
                pass

        except Exception as e:
            logger.error("Stream generation failed", error=str(e))
            error_data = json.dumps({"error": str(e), "done": True})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
