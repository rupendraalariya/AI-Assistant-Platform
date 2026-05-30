# 🤖 AI Assistant Platform

> A production-grade **Multi-AI Chat Platform** combining the best of ChatGPT, Claude, Perplexity, and OpenRouter — with RAG document chat, 8 AI providers, smart routing, streaming, and Google authentication.

[![CI Pipeline](https://github.com/RupendraAlariya/ai-assistant-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/RupendraAlariya/ai-assistant-platform/actions)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

### Multi-AI Provider System
- **8 providers**: OpenAI, Google Gemini, Anthropic Claude, Groq, DeepSeek, Mistral, Together AI, Ollama
- **Dynamic model selector** — switch models per provider in real time
- **Smart routing** — auto-selects the best provider by intent (coding → DeepSeek, fast → Groq, research → Gemini, reasoning → GPT)
- **Graceful fallback** — if one provider fails, automatically cascades to the next; users never see a server error

### RAG Document Chat
- Upload **PDF, DOCX, TXT, CSV** and chat with your documents
- Pipeline: extract → chunk → embed (HuggingFace) → store in **FAISS** → retrieve → inject context
- Per-user document isolation, document management UI (view / delete / reindex)

### ChatGPT-Grade UI
- Real-time **streaming** responses with typing indicator
- **Professional code blocks** — syntax highlighting, language badge, copy button, line numbers
- Message actions — edit, delete, copy, regenerate, like/dislike, share
- Chat management — search, pin, rename, export, context menus
- Dark / Light / System themes, fully responsive, Framer Motion animations

### Authentication & Security
- JWT auth with **access + refresh tokens** and automatic refresh
- **Google OAuth** (Sign in with Google) via Authlib
- bcrypt password hashing, CSRF-protected OAuth flow
- All secrets server-side only — never exposed to the frontend

### Production Engineering
- Adaptive memory with Redis (optional) + graceful in-memory fallback
- Token & cost tracking, analytics dashboard
- Lazy loading + code splitting, structured JSON logging
- Docker Compose, GitHub Actions CI

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────────────────────────────────┐
│  React +     │────▶│              FastAPI Backend                   │
│  TypeScript  │◀────│                                                │
│  + Tailwind  │ SSE │  Auth │ Chat │ RAG │ LLM Router │ Analytics    │
└──────────────┘     └───────┬──────────────┬───────────────┬────────┘
                             │              │               │
                    ┌────────┴───┐   ┌──────┴─────┐   ┌─────┴──────┐
                    │ PostgreSQL │   │   Redis    │   │   FAISS    │
                    │  /SQLite   │   │ (optional) │   │  Vectors   │
                    └────────────┘   └────────────┘   └────────────┘
                             │
                    ┌────────┴─────────────────────────────────────┐
                    │  LLM Router  →  OpenAI · Gemini · Claude ·     │
                    │  Groq · DeepSeek · Mistral · Together · Ollama │
                    └───────────────────────────────────────────────┘
```

**Why one provider class covers 7 services:** OpenAI, Gemini, Groq, DeepSeek, Mistral, Together, and Ollama all expose OpenAI-compatible endpoints, so a single client with swappable base URLs handles them all (the OpenRouter approach). Only Claude uses a dedicated Anthropic client.

---

## 📸 Screenshots

> _Add screenshots here once deployed:_
>
> | Chat Interface | Compare Mode | RAG Document Chat |
> |:---:|:---:|:---:|
> | ![chat](docs/screenshots/chat.png) | ![compare](docs/screenshots/compare.png) | ![rag](docs/screenshots/rag.png) |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Zustand, Framer Motion, Vite |
| **Backend** | FastAPI, Python 3.12, SQLAlchemy (async), Pydantic |
| **AI / ML** | LangChain, OpenAI SDK, Anthropic SDK, HuggingFace Embeddings, FAISS |
| **Database** | PostgreSQL / SQLite, Redis (optional) |
| **Auth** | JWT (python-jose), bcrypt, Google OAuth (Authlib) |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## 🚀 Installation

### Prerequisites
- Python 3.12+
- Node.js 20+
- (Optional) Docker, PostgreSQL, Redis

### 1. Clone & configure

```bash
git clone https://github.com/RupendraAlariya/ai-assistant-platform.git
cd ai-assistant-platform
cp .env.example .env
# Edit .env and add at least one provider API key (Groq is free & fast)
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs at **http://localhost:8000** (Swagger docs at `/docs`).

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**.

### 4. (Optional) Run everything with Docker

```bash
docker-compose up -d --build
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in the values you have.

| Variable | Required | Description |
|----------|:---:|-------------|
| `OPENAI_API_KEY` | optional | OpenAI API key |
| `GEMINI_API_KEY` | optional | Google Gemini key |
| `ANTHROPIC_API_KEY` | optional | Claude key |
| `GROQ_API_KEY` | optional | Groq key (free, recommended for testing) |
| `DEEPSEEK_API_KEY` | optional | DeepSeek key |
| `MISTRAL_API_KEY` | optional | Mistral key |
| `JWT_SECRET_KEY` | **yes** | Secret for signing JWTs |
| `SESSION_SECRET_KEY` | **yes** | Secret for OAuth session cookies |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | optional | For Google login |
| `DATABASE_URL` | **yes** | SQLite (default) or PostgreSQL |
| `REDIS_URL` | optional | Falls back to in-memory if unavailable |

> At least **one provider key** is needed for chat. Email/password and the full UI work without any keys.

---

## ☁️ Deployment

| Component | Recommended Host |
|-----------|------------------|
| Backend | Render / Railway / AWS ECS (Docker) |
| Frontend | Vercel / Netlify |
| Database | Render PostgreSQL / AWS RDS / Supabase |
| Redis | Render Redis / Upstash (optional) |

**Backend (Render):** create a Web Service from `backend/`, runtime Docker, add env vars from `.env.example`.
**Frontend (Vercel):** import repo, root `frontend/`, set `VITE_API_URL=https://your-backend-url/api/v1`.

See [`docs/deployment.md`](docs/deployment.md) for the full guide.

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

Covers auth (register/login/refresh/logout/Google), the LLM router (smart routing + fallback), and core utilities.

---

## 🗺️ Future Improvements

- [ ] RAGAS-based retrieval evaluation
- [ ] Semantic caching to cut token costs
- [ ] WebSocket multiplexing for compare mode streaming
- [ ] Voice input / TTS output
- [ ] Per-document citations with source highlighting
- [ ] Team workspaces & shared chats

---

## 👤 Author

**Rupendra Alariya**
Full-Stack & AI Engineer

[GitHub](https://github.com/RupendraAlariya) · [LinkedIn](https://linkedin.com/in/rupendra-alariya) · [Portfolio](https://rupendra.dev)

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

_All Rights Reserved © 2026 Rupendra Alariya_
