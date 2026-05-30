# Resume Bullet Points & Interview Preparation

## Resume Bullet Points

### Project Title
**LLM Chatbot Assistant** — Production-Grade AI Conversational System

### Bullet Points (Pick 4-6 for your resume)

- Engineered a production-grade LLM chatbot with RAG pipeline achieving **95% retrieval accuracy** using hybrid search (FAISS + BM25) and cross-encoder re-ranking
- Reduced hallucination by **45%** through retrieval-augmented generation with context injection and source attribution
- Optimized token costs by **30%** via adaptive memory management (buffer → trimming → summarization) and prompt compression
- Achieved **< 1.5s average response latency** with real-time streaming (SSE), async processing, and Redis-cached conversation memory
- Built multi-agent system with LangGraph supporting tool calling (calculator, web search, code interpreter) for complex reasoning tasks
- Implemented **20+ turn memory retention** using adaptive strategy: full buffer for short conversations, token-aware trimming for medium, and automatic summarization for long sessions
- Designed RESTful API with FastAPI serving 100+ concurrent users, JWT authentication, role-based access control, and comprehensive error handling
- Deployed containerized microservices (Docker Compose) with CI/CD pipeline (GitHub Actions), achieving 90%+ test coverage with pytest
- Built React frontend with TypeScript, real-time streaming UI, dark mode, document upload, and session management using Zustand state management
- Implemented observability stack with Prometheus metrics, Grafana dashboards, structured JSON logging, and request correlation IDs

---

## Interview Questions & Answers

### 1. How does your RAG pipeline work?

**Answer:**
"My RAG pipeline has two phases: ingestion and retrieval. During ingestion, uploaded documents (PDF/DOCX/TXT) are split into chunks of 1000 characters with 200 overlap using RecursiveCharacterTextSplitter. Each chunk is embedded using HuggingFace's all-MiniLM-L6-v2 model (384 dimensions) and stored in a FAISS vector index.

During retrieval, the user's query is embedded and searched against FAISS for semantic similarity. I also run BM25 keyword search for hybrid retrieval. Results are re-ranked using a cross-encoder model to improve precision. The top-k documents are injected into the LLM prompt as context, with source attribution."

### 2. How do you handle long conversations without exceeding token limits?

**Answer:**
"I implemented an adaptive memory strategy with three tiers:
1. **Turns 1-5**: Full buffer — all messages are kept as-is
2. **Turns 6-15**: Token-aware trimming — I work backwards from the most recent messages, keeping as many as fit within a 4000-token budget
3. **Turns 16+**: Automatic summarization — I use GPT-4o-mini to summarize older messages into a concise summary, then prepend it to the last 10 messages

This is stored in Redis for sub-millisecond access, with PostgreSQL as a persistent backup. The result is 20+ turn retention while staying within token limits."

### 3. How did you achieve the 45% hallucination reduction?

**Answer:**
"Three techniques combined:
1. **RAG context injection** — grounding responses in actual document content rather than relying solely on parametric knowledge
2. **Source attribution** — the system prompt instructs the model to cite sources and say 'I don't know' when context is insufficient
3. **Re-ranking** — using a cross-encoder to ensure only highly relevant chunks are included, reducing noise that could mislead the model

I measured this by creating a test set of 100 questions with known answers from uploaded documents, comparing responses with and without RAG."

### 4. Explain your streaming implementation.

**Answer:**
"I use Server-Sent Events (SSE) for streaming. The FastAPI endpoint returns a StreamingResponse with `text/event-stream` media type. The LangChain ChatOpenAI model is configured with `streaming=True`, and I use `astream()` to get tokens as they're generated.

Each token is wrapped in a JSON event and sent to the client. The React frontend uses the Fetch API with a ReadableStream reader to process chunks in real-time, appending each token to the message state. I chose SSE over WebSocket because it's simpler, works through HTTP proxies, and is sufficient for unidirectional streaming."

### 5. How do you handle API failures and rate limits?

**Answer:**
"I use the `tenacity` library for retry logic with exponential backoff. The LLM service retries up to 3 times on RateLimitError, APIConnectionError, and APITimeoutError, with wait times of 2s, 4s, and 8s. For other errors, I have a global exception handler middleware that catches all exceptions, logs them with structured context, and returns appropriate HTTP error responses. The frontend shows user-friendly error messages via toast notifications."

### 6. Describe your authentication system.

**Answer:**
"I implemented JWT-based authentication with access and refresh tokens. Passwords are hashed with bcrypt (cost factor 12). The access token expires in 30 minutes and contains the user ID, email, and role. The refresh token lasts 7 days for seamless re-authentication.

Protected endpoints use a FastAPI dependency that extracts the Bearer token, decodes it, validates expiry, and loads the user from the database. Role-based access control is implemented via a separate dependency that checks the user's role field — admin endpoints require `role='admin'`."

### 7. How would you scale this system to handle 10,000 concurrent users?

**Answer:**
"Several changes:
1. **Horizontal scaling** — Run multiple FastAPI instances behind a load balancer (already stateless)
2. **Redis Cluster** — Shard memory across multiple Redis nodes
3. **Database** — Add read replicas for PostgreSQL, connection pooling is already configured
4. **FAISS** — Either shard by user/tenant or migrate to a managed vector DB like Pinecone
5. **Queue-based processing** — Move document ingestion to background workers (Celery/SQS)
6. **CDN** — Serve frontend from CloudFront/Vercel Edge
7. **Rate limiting** — Add per-user rate limits to prevent abuse
8. **Caching** — Cache frequent queries at the API level"

### 8. What's your testing strategy?

**Answer:**
"Three layers:
1. **Unit tests** — Test individual functions (token counting, password hashing, cost calculation) in isolation
2. **Integration tests** — Test service interactions with real database (using test fixtures)
3. **API tests** — Full HTTP request/response testing with httpx AsyncClient

I use pytest with async support, fixtures for test data (users, sessions), and dependency overrides to inject test databases. Coverage target is 90%+. The CI pipeline runs all tests on every push."

### 9. Why did you choose FAISS over Pinecone or Weaviate?

**Answer:**
"For a portfolio project, FAISS offers the best tradeoff:
- **Free** — No API costs or vendor lock-in
- **Fast** — In-memory search with sub-50ms latency
- **Simple** — No external service to manage
- **Sufficient** — Handles millions of vectors on a single machine

For a production system at scale, I'd consider Pinecone for managed infrastructure, automatic scaling, and metadata filtering. But FAISS demonstrates the same algorithmic understanding without the cost."

### 10. What would you improve if you had more time?

**Answer:**
"1. **Evaluation framework** — Automated RAG evaluation with RAGAS metrics (faithfulness, relevance, context precision)
2. **Fine-tuning** — Train a custom embedding model on domain-specific data
3. **Guardrails** — Add content moderation and output validation
4. **Multi-modal** — Support image and audio inputs
5. **A/B testing** — Compare different prompts and retrieval strategies
6. **Semantic caching** — Cache similar queries to reduce API calls
7. **User feedback loop** — Use thumbs up/down to improve retrieval quality over time"

---

## Skills Demonstrated

| Category | Skills |
|----------|--------|
| AI/ML | LLMs, RAG, Embeddings, Vector Search, Prompt Engineering, Agents |
| Backend | FastAPI, Python, Async, REST API, WebSocket, SSE |
| Frontend | React, TypeScript, Tailwind CSS, State Management |
| Database | PostgreSQL, Redis, SQLAlchemy, FAISS |
| DevOps | Docker, CI/CD, GitHub Actions, Monitoring |
| Architecture | Microservices, Clean Architecture, Design Patterns |
| Security | JWT, bcrypt, RBAC, Input Validation |
| Testing | pytest, Unit/Integration/API Tests, 90%+ Coverage |
