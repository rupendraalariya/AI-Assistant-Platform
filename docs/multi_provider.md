# Multi-AI Provider Platform

This document describes the multi-provider architecture that turns the chatbot
into a ChatHub/Poe/OpenRouter-style platform.

## Supported Providers

| Provider | Models | API Key Env Var | Notes |
|----------|--------|-----------------|-------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo | `OPENAI_API_KEY` | |
| Google Gemini | gemini-2.0-flash, gemini-1.5-flash/pro | `GEMINI_API_KEY` | OpenAI-compatible endpoint |
| Anthropic Claude | claude-3.5-sonnet/haiku, claude-3-opus | `ANTHROPIC_API_KEY` | Native Anthropic SDK |
| Groq | llama-3.3-70b, llama-3.1-8b, qwen, mixtral | `GROQ_API_KEY` | Ultra-fast inference |
| DeepSeek | deepseek-chat, deepseek-reasoner | `DEEPSEEK_API_KEY` | Great for coding |
| Mistral | mistral-large/small, nemo | `MISTRAL_API_KEY` | |
| Together AI | Llama 3.3, Mixtral, Qwen | `TOGETHER_API_KEY` | |
| Ollama | llama3.2, qwen2.5, deepseek-coder | `OLLAMA_BASE_URL` | Local, no key needed |

## Architecture

```
User
  ↓
FastAPI  (/api/v1/chat/multi)
  ↓
LLMRouter  (app/services/llm_router.py)
  ├── resolve_provider_and_model()   ← smart routing
  ├── _build_fallback_order()        ← fallback chain
  │
  ├── OpenAICompatibleProvider  → OpenAI, Gemini, Groq,
  │                                DeepSeek, Mistral, Together, Ollama
  └── ClaudeProvider            → Anthropic (native SDK)
```

### Why one provider class covers seven services

OpenAI, Gemini, Groq, DeepSeek, Mistral, Together, and Ollama all expose the
**same `/chat/completions` API shape**. We use the official `openai` SDK and
just swap the `base_url`. This is exactly how OpenRouter works and keeps the
codebase DRY. Only Claude needs a separate class because its Messages API
treats the system prompt as a top-level parameter.

## Smart Routing (provider = "auto")

When the request provider is `"auto"`, the router detects intent from the prompt
and routes to the best provider. If that provider has no API key configured, it
gracefully falls back to the default provider.

| Intent | Detected by keywords | Routed to |
|--------|---------------------|-----------|
| coding | code, function, debug, python, error, sql... | DeepSeek |
| research | research, analyze, comprehensive, in-depth... | Claude Sonnet |
| reasoning | why, prove, solve, calculate, step by step... | GPT-4o |
| simple | (< 12 words) | Gemini Flash |
| fast | (everything else) | Groq |

## Fallback System

If the chosen provider errors out, the router walks the fallback chain:

```
groq → gemini → deepseek → openai → mistral → together
```

Only configured providers are tried. If **all** fail, the user gets a friendly
message instead of a 500 error.

## API Endpoints

### List providers
```
GET /api/v1/providers
```

### List models for a provider
```
GET /api/v1/providers/{provider_id}/models
```

### Chat (non-streaming)
```
POST /api/v1/chat/multi
{
  "message": "Explain transformers",
  "provider": "groq",          // or "auto"
  "model": "llama-3.3-70b-versatile",
  "enable_fallback": true
}
```

### Chat (streaming SSE)
```
POST /api/v1/chat/multi/stream
```
Streams events:
```
data: {"meta": true, "provider": "groq", "model": "..."}
data: {"content": "Transformers", "done": false, "provider": "groq"}
...
data: {"content": "", "done": true, "provider": "groq", "model": "..."}
```

### Compare mode
```
POST /api/v1/chat/compare
{
  "message": "Explain transformers",
  "providers": [
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "claude", "model": "claude-3-5-sonnet-20241022"},
    {"provider": "gemini", "model": "gemini-2.0-flash"},
    {"provider": "deepseek", "model": "deepseek-chat"}
  ]
}
```
Runs all providers **concurrently** with `asyncio.gather` and returns
side-by-side results with per-provider tokens, latency, and cost.

## Security

- All API keys live in backend `.env` only.
- Keys are **never** sent to the frontend.
- The frontend only ever sees provider IDs and model names.
- All provider calls are proxied through the backend.

## Adding a New Provider

1. Add a `ProviderConfig` entry to `app/services/providers/registry.py`.
2. If it's OpenAI-compatible, you're done — no code needed.
3. If it has a custom API, create a class extending `BaseLLMProvider`
   and wire it into `factory.py`.

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `ModelSelector.tsx` | Provider + model dropdowns in the header |
| `CompareMode.tsx` | Side-by-side multi-provider comparison |
| `providerStore.ts` | Zustand store for provider/model state |
| `ChatMessage.tsx` | Shows provider badge on each AI response |
