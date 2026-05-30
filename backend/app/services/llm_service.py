"""LLM Service - OpenAI GPT integration with retry handling and streaming."""

import time
from typing import AsyncGenerator, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.token_counter import count_tokens, estimate_cost

logger = get_logger(__name__)
settings = get_settings()

# System prompt for the chatbot
SYSTEM_PROMPT = """You are an intelligent AI assistant. You provide helpful, accurate, and concise responses.
When answering questions based on provided context, cite the relevant information.
If you don't know something, say so honestly rather than making up information.
Be conversational but professional."""


class LLMService:
    """Service for interacting with OpenAI LLM models."""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.model = model or settings.openai_model
        self.temperature = temperature if temperature is not None else settings.openai_temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens
        self._llm = None
        self._streaming_llm = None

    def _get_llm(self):
        """Lazy-load LLM to avoid import errors if openai not installed."""
        if self._llm is None:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=settings.openai_api_key,
                streaming=False,
            )
        return self._llm

    def _get_streaming_llm(self):
        """Lazy-load streaming LLM."""
        if self._streaming_llm is None:
            from langchain_openai import ChatOpenAI
            self._streaming_llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=settings.openai_api_key,
                streaming=True,
            )
        return self._streaming_llm

    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        """Generate a non-streaming response from the LLM."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        start_time = time.time()

        messages = self._build_messages(
            user_message=user_message,
            chat_history=chat_history or [],
            context=context,
            system_prompt=system_prompt or SYSTEM_PROMPT,
        )

        try:
            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            latency_ms = int((time.time() - start_time) * 1000)

            # Calculate tokens
            prompt_tokens = count_tokens(str(messages), self.model)
            completion_tokens = count_tokens(response.content, self.model)
            total_tokens = prompt_tokens + completion_tokens
            cost = estimate_cost(prompt_tokens, completion_tokens, self.model)

            logger.info(
                "LLM response generated",
                model=self.model,
                tokens=total_tokens,
                latency_ms=latency_ms,
                cost=cost,
            )

            return {
                "content": response.content,
                "tokens_used": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": latency_ms,
                "cost": cost,
                "model": self.model,
            }

        except Exception as e:
            logger.error("LLM generation failed", error=str(e), model=self.model)
            raise

    async def generate_stream(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        messages = self._build_messages(
            user_message=user_message,
            chat_history=chat_history or [],
            context=context,
            system_prompt=system_prompt or SYSTEM_PROMPT,
        )

        try:
            llm = self._get_streaming_llm()
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error("LLM streaming failed", error=str(e))
            raise

    def _build_messages(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]],
        context: Optional[str],
        system_prompt: str,
    ) -> List:
        """Build the message list for the LLM."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages = []

        # System message with optional RAG context
        if context:
            enhanced_prompt = (
                f"{system_prompt}\n\n"
                f"Use the following context to answer the user's question:\n"
                f"---\n{context}\n---\n"
                f"If the context doesn't contain relevant information, "
                f"say so and answer based on your general knowledge."
            )
            messages.append(SystemMessage(content=enhanced_prompt))
        else:
            messages.append(SystemMessage(content=system_prompt))

        # Chat history
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Current user message
        messages.append(HumanMessage(content=user_message))

        return messages

    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize a conversation for memory compression."""
        from langchain_core.messages import HumanMessage

        summary_prompt = (
            "Summarize the following conversation concisely, "
            "preserving key facts, decisions, and context:\n\n"
        )
        for msg in messages:
            summary_prompt += f"{msg['role'].upper()}: {msg['content']}\n"

        llm = self._get_llm()
        response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
        return response.content


def get_llm_service(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> LLMService:
    """Factory function for LLM service."""
    return LLMService(model=model, temperature=temperature, max_tokens=max_tokens)
