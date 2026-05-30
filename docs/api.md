# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Health Check

```http
GET /health
```

**Response 200:**
```json
{
  "status": "healthy",
  "service": "LLM Chatbot Assistant",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### Authentication

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepass123"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Get Profile
```http
GET /auth/me
Authorization: Bearer <token>
```

---

### Chat

#### Send Message
```http
POST /chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What is machine learning?",
  "session_id": "uuid (optional)",
  "use_rag": false,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "role": "assistant",
  "content": "Machine learning is...",
  "tokens_used": 150,
  "latency_ms": 1200,
  "model": "gpt-4o-mini",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Stream Message (SSE)
```http
POST /chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Explain quantum computing",
  "session_id": "uuid (optional)",
  "use_rag": true
}
```

**Response: text/event-stream**
```
data: {"content": "Quantum", "done": false}
data: {"content": " computing", "done": false}
data: {"content": " is", "done": false}
...
data: {"content": "", "done": true, "session_id": "uuid", "tokens_used": 200}
```

---

### Sessions

#### Create Session
```http
POST /sessions
Authorization: Bearer <token>

{"title": "My Chat", "model": "gpt-4o-mini"}
```

#### List Sessions
```http
GET /sessions
Authorization: Bearer <token>
```

#### Delete Session
```http
DELETE /sessions/{session_id}
Authorization: Bearer <token>
```

#### Get Chat History
```http
GET /sessions/{session_id}/history
Authorization: Bearer <token>
```

---

### Documents

#### Upload Document
```http
POST /documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

**Supported formats:** PDF, DOCX, TXT (max 10MB)

#### List Documents
```http
GET /documents
Authorization: Bearer <token>
```

---

### Analytics

#### User Usage
```http
GET /analytics/usage
Authorization: Bearer <token>
```

#### Cost Breakdown
```http
GET /analytics/costs
Authorization: Bearer <token>
```

#### System Metrics (Admin)
```http
GET /analytics/system
Authorization: Bearer <admin_token>
```

---

## Error Responses

All errors follow this format:
```json
{
  "error": "Error message",
  "detail": "Additional details",
  "status_code": 400
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |
