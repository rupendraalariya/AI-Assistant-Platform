# Authentication Guide

This app supports two authentication methods:
1. **Traditional** — email/password with bcrypt hashing + JWT
2. **Google OAuth** — Sign in / Sign up with Google

## Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/auth/register` | POST | No | Create account (email + password) |
| `/api/v1/auth/login` | POST | No | Login, returns access + refresh tokens |
| `/api/v1/auth/refresh` | POST | No | Exchange refresh token for new token pair |
| `/api/v1/auth/logout` | POST | Yes | Logout (client clears tokens) |
| `/api/v1/auth/me` | GET | Yes | Current user profile |
| `/api/v1/auth/google/login` | GET | No | Start Google OAuth flow |
| `/api/v1/auth/google/callback` | GET | No | Google redirect target |

## Database Schema (users table)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID (string) | Primary key |
| email | string | Unique |
| username | string | Unique, auto-generated for Google users |
| hashed_password | string | **null** for Google-only accounts |
| google_id | string | Google `sub` claim, unique |
| auth_provider | string | `local` or `google` |
| profile_picture | string | Google avatar URL |
| is_active | bool | |
| created_at | datetime | |

## JWT Tokens

- **Access token**: short-lived (30 min default), sent as `Authorization: Bearer <token>`
- **Refresh token**: long-lived (7 days default), used to get new access tokens
- Tokens are signed with `JWT_SECRET_KEY` using HS256
- The frontend automatically refreshes the access token on a 401 (see `api.ts` interceptor)

## Google OAuth Flow

```
User clicks "Continue with Google"
   ↓
Browser → GET /api/v1/auth/google/login
   ↓
Backend redirects to Google consent screen (Authlib, CSRF state in session cookie)
   ↓
User approves
   ↓
Google → GET /api/v1/auth/google/callback?code=...
   ↓
Backend exchanges code for tokens, reads userinfo (sub, email, name, picture)
   ↓
AuthService.authenticate_google():
   1. google_id match? → log in
   2. email match?     → link Google to existing account
   3. neither?         → create new account
   ↓
Backend redirects → http://localhost:3000/auth/callback?access_token=...&refresh_token=...
   ↓
Frontend AuthCallbackPage stores tokens, loads profile, redirects to /
```

## Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth client ID**
5. Configure the OAuth consent screen if prompted (External, add your email as test user)
6. Application type: **Web application**
7. Add **Authorized redirect URI**:
   ```
   http://localhost:8000/api/v1/auth/google/callback
   ```
8. Copy the **Client ID** and **Client Secret** into your `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
   FRONTEND_URL=http://localhost:3000
   SESSION_SECRET_KEY=any-long-random-string
   ```
9. Restart the backend. The "Continue with Google" button will now work.

> If Google credentials are not set, the Google button returns a 503 with a clear
> message, and email/password auth continues to work normally.

## Security Notes

- Passwords hashed with **bcrypt** (cost factor 12), truncated safely to 72 bytes
- Google **id_token verified** by Authlib against Google's JWKS (OIDC discovery)
- OAuth **CSRF protection** via signed session state cookie (SessionMiddleware)
- API keys / secrets live only in backend `.env`, never exposed to the frontend
- Refresh tokens are typed (`type: refresh`) so they can't be used as access tokens
- Input validation via Pydantic (email format, password length 8-128)

## Production Hardening (recommended next steps)

- Store tokens in httpOnly cookies instead of localStorage (mitigates XSS)
- Add a Redis token blacklist for true server-side logout
- Set `https_only=True` on SessionMiddleware (already auto-enabled in production env)
- Rotate `JWT_SECRET_KEY` and `SESSION_SECRET_KEY` to strong random values
