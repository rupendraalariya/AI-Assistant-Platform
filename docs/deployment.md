# Deployment Guide

## Deployment Options

### Option 1: Docker Compose (Recommended for Demo)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/llm-chatbot-assistant.git
cd llm-chatbot-assistant

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up -d --build

# 4. Verify
curl http://localhost:8000/api/v1/health
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

---

### Option 2: Render (Free Tier)

#### Backend Deployment

1. Create a new **Web Service** on Render
2. Connect your GitHub repository
3. Configure:
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Environment Variables**:
     - `OPENAI_API_KEY`
     - `JWT_SECRET_KEY`
     - `DATABASE_URL` (from Render PostgreSQL)
     - `REDIS_URL` (from Render Redis)

4. Create a **PostgreSQL** database on Render
5. Create a **Redis** instance on Render
6. Update environment variables with connection strings

#### Frontend Deployment (Vercel)

1. Import project to Vercel
2. Set root directory to `frontend`
3. Add environment variable:
   - `VITE_API_URL=https://your-backend.onrender.com/api/v1`
4. Deploy

---

### Option 3: AWS (Production)

#### Infrastructure

```
┌─────────────────────────────────────────────┐
│                    AWS                        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   ECS    │  │   RDS    │  │ElastiCache│  │
│  │ (Fargate)│  │(Postgres)│  │  (Redis)  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│       │                                      │
│  ┌──────────┐  ┌──────────┐                 │
│  │   ALB    │  │    S3    │                 │
│  │          │  │ (FAISS)  │                 │
│  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────┘
```

Steps:
1. Push Docker image to ECR
2. Create ECS Fargate service
3. Provision RDS PostgreSQL
4. Provision ElastiCache Redis
5. Configure ALB with SSL
6. Deploy frontend to CloudFront + S3

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET_KEY` | Yes | Secret for JWT signing |
| `CORS_ORIGINS` | Yes | Allowed frontend origins |
| `ENVIRONMENT` | No | development/production |
| `DEBUG` | No | Enable debug mode |

---

## SSL/TLS

For production, always use HTTPS:
- Render: Automatic SSL
- AWS: ACM certificate on ALB
- Vercel: Automatic SSL

---

## Monitoring

### Prometheus Metrics
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `llm_tokens_total` - Total LLM tokens used
- `active_sessions` - Current active sessions

### Grafana Dashboards
Access at http://localhost:3001 (admin/admin)
- System Overview
- API Performance
- LLM Usage & Costs
- User Analytics

---

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
```

### Database Scaling
- Read replicas for PostgreSQL
- Redis Cluster for memory

### Performance Tips
- Enable response caching for repeated queries
- Use connection pooling (already configured)
- Implement rate limiting per user
- Use CDN for frontend assets
