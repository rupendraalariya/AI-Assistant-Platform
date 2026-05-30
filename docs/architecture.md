# Architecture Documentation

## System Overview

The LLM Chatbot Assistant is a production-grade conversational AI system built with a microservices-inspired architecture. It combines retrieval-augmented generation (RAG), adaptive memory management, real-time streaming, and multi-agent capabilities.

## Component Architecture

### 1. API Layer (FastAPI)
- **Versioned routing** (`/api/v1/`) for backward compatibility
- **Middleware stack**: Logging → Exception Handling → CORS
- **Dependency injection** for database sessions, auth, and services
- **Async throughout** for high concurrency

### 2. Service Layer
- **LLM Service**: OpenAI integration with retry logic, streaming, and cost tracking
- **Memory Service**: Redis-backed adaptive memory (buffer → trim → summarize)
- **RAG Service**: Document ingestion, vector search, and context injection
- **Auth Service**: JWT token management and user operations
- **Analytics Service**: Usage metrics and cost tracking
- **Agent Service**: Multi-agent system with tool calling

### 3. Data Layer
- **PostgreSQL**: Persistent storage (users, sessions, chats, documents)
- **Redis**: Session memory, caching, real-time state
- **FAISS**: Vector embeddings for semantic search

### 4. Frontend
- **React 18** with TypeScript
- **Zustand** for state management
- **Tailwind CSS** for styling
- **SSE** for real-time streaming

## Design Patterns

| Pattern | Usage |
|---------|-------|
| Repository | Database access abstraction |
| Service | Business logic encapsulation |
| Factory | Service instantiation |
| Dependency Injection | FastAPI Depends() |
| Observer | SSE streaming |
| Strategy | Adaptive memory selection |
| Singleton | RAG service, Redis client |

## Data Flow

### Chat Request Flow
1. Client sends message via HTTP POST
2. Auth middleware validates JWT
3. Chat endpoint receives request
4. Memory service loads conversation context from Redis
5. RAG service retrieves relevant documents (if enabled)
6. Cost service compresses context to fit token budget
7. LLM service generates response (with retry logic)
8. Memory service saves new messages
9. Analytics service tracks tokens and cost
10. Response returned to client

### Streaming Flow
1. Client opens SSE connection
2. LLM generates tokens incrementally
3. Each token sent as SSE event
4. Client renders tokens in real-time
5. Final event includes metadata (tokens, session_id)

## Scalability Considerations

- **Horizontal scaling**: Stateless API servers behind load balancer
- **Redis clustering**: For memory at scale
- **FAISS sharding**: Split vector index by user/document
- **Connection pooling**: SQLAlchemy async pool (20 connections)
- **Background tasks**: Document processing can be offloaded to workers
