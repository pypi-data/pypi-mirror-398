# Authentication

FastroAI provides four authentication mechanisms: sessions, JWT tokens, OAuth, and API keys. Sessions are the default and recommended for most applications.

## When to Use What

| Mechanism | Best For | Why |
|-----------|----------|-----|
| **Sessions** | Web apps, SPAs, most cases | CSRF protection, device tracking, server-controlled logout |
| **JWT** | Mobile apps, external API clients | Stateless, no cookies needed |
| **OAuth** | "Login with Google/GitHub" | Social login, delegates auth to provider |
| **API Keys** | Third-party developers, integrations | Long-lived, usage tracking, per-key rate limits |

**Start with sessions.** All built-in FastroAI routes use session authentication. Only switch to JWT if you're building for mobile apps or need stateless auth for a specific reason.

OAuth creates a session after login, so OAuth users get all the session benefits too.

API keys are covered in the [Access Control](../access-control/index.md) guide since they're about programmatic access rather than user login.

## Configuration

Auth settings are read from your `backend/.env` file and defined in `AuthSettings` (`backend/src/infrastructure/config/settings.py:225`).

### JWT

Used for signing and validating tokens. The `SECRET_KEY` is critical and must be changed in production.

```bash
SECRET_KEY=your-production-secret-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Sessions

Controls session storage, timeouts, and security. Redis is recommended for production. Rate limiting protects against brute force login attempts.

```bash
SESSION_BACKEND=redis
SESSION_TIMEOUT_MINUTES=30
MAX_SESSIONS_PER_USER=5
SESSION_SECURE_COOKIES=true
CSRF_ENABLED=true
LOGIN_MAX_ATTEMPTS=5
LOGIN_WINDOW_MINUTES=15
```

### OAuth

Credentials for social login providers. See [OAuth Providers](oauth-providers.md) for setup instructions.

```bash
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
OAUTH_REDIRECT_BASE_URL=http://localhost:8000
```

## In This Section

- **[Sessions](sessions.md)** - Session-based auth, CSRF, device tracking, rate limiting
- **[JWT Tokens](jwt.md)** - Stateless token auth for mobile and external clients
- **[OAuth Providers](oauth-providers.md)** - Google/GitHub login, adding new providers

## Key Files

| Component | Location |
|-----------|----------|
| Session dependencies | `backend/src/infrastructure/auth/session/dependencies.py` |
| Session manager | `backend/src/infrastructure/auth/session/manager.py` |
| JWT dependencies | `backend/src/infrastructure/auth/jwt/dependencies.py` |
| JWT security | `backend/src/infrastructure/auth/jwt/security.py` |
| OAuth providers | `backend/src/infrastructure/auth/oauth/providers/` |
| Auth settings | `backend/src/infrastructure/config/settings.py:225-250` |

---

[Start with Sessions →](sessions.md){ .md-button .md-button--primary }
