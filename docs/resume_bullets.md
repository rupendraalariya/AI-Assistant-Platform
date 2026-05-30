# Resume Bullet Points — AI Assistant Platform

Pick 3-5 that best fit the role you're applying for.

## Concise (one-liners)
- Built a production-grade **Multi-AI chat platform** (FastAPI + React) integrating **8 LLM providers** with smart routing and automatic failover.
- Implemented **RAG document chat** (PDF/DOCX/TXT/CSV) using HuggingFace embeddings + **FAISS**, enabling context-aware answers from user-uploaded files.
- Engineered **real-time token streaming** over SSE with a ChatGPT-style UI featuring syntax-highlighted code blocks, edit/regenerate, and compare mode.

## Impact-focused (detailed)
- Designed a **provider router** that auto-selects the optimal LLM by query intent (coding → DeepSeek, fast → Groq, reasoning → GPT) and gracefully cascades through a fallback chain, eliminating user-facing 503 errors.
- Architected a **DRY multi-provider layer** using the OpenAI-compatible API pattern — one client class serves 7 providers via swappable base URLs, plus a dedicated Anthropic adapter.
- Implemented **JWT auth with refresh-token rotation** and **Google OAuth** (Authlib), with bcrypt hashing and CSRF-protected session flow; all secrets kept server-side.
- Built an **adaptive memory system** (buffer → token-trim → summarization) backed by Redis with a graceful in-memory fallback, supporting 20+ turn conversations.
- Set up **CI/CD with GitHub Actions** (lint, build, test, secret scanning) and **Docker Compose** for one-command local deployment.

## Tech stack line (for skills section)
`React · TypeScript · Tailwind · FastAPI · Python · LangChain · FAISS · PostgreSQL · Redis · Docker · JWT · OAuth · GitHub Actions`

---

## Interview talking points
- **Why one class for 7 providers?** They share the OpenAI `/chat/completions` shape; swap `base_url`. Same approach OpenRouter uses — keeps the code DRY and adding a provider is a config-only change.
- **How does fallback work?** The router tries the primary provider, and on any exception cascades through an ordered chain of configured providers, only surfacing a friendly message if all fail.
- **How is RAG wired?** Documents are chunked, embedded, and stored in FAISS with per-user metadata. On each message the backend retrieves relevant chunks (filtered by user), compresses them to a token budget, and injects them into the system prompt.
- **Security?** API keys live only in `.env` (gitignored); the frontend never sees them — all provider calls are proxied through the backend.
