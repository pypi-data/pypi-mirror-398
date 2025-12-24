# Sessions

Sessions are FastroAI's default authentication mechanism. All built-in API routes use session auth.

## Protecting Routes

Import the session dependencies and add them to your routes:

```python
from fastapi import APIRouter, Depends

from src.infrastructure.auth.session.dependencies import get_current_user

router = APIRouter()

@router.get("/my-profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["id"], "email": current_user["email"]}
```

If the request doesn't have a valid session, FastroAI returns 401 Unauthorized.

### Available Dependencies

**`get_current_user`** - Returns the authenticated user. Raises 401 if not authenticated.

```python
@router.get("/dashboard")
async def dashboard(current_user: dict = Depends(get_current_user)):
    return {"welcome": current_user["username"]}
```

**`get_current_superuser`** - Same as above, but also checks `is_superuser=True`. Raises 403 if not a superuser.

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_superuser),
):
    # Only superusers reach this code
    ...
```

**`get_optional_user`** - Returns the user if authenticated, `None` otherwise. Never raises.

```python
@router.get("/products")
async def list_products(current_user: dict | None = Depends(get_optional_user)):
    if current_user:
        # Personalize for logged-in users
        ...
```

### Protecting Entire Routers

Apply auth to all routes in a router:

```python
router = APIRouter(
    prefix="/api/v1/admin",
    dependencies=[Depends(get_current_superuser)],
)

@router.get("/stats")
async def stats():
    # Already authenticated at router level
    ...
```

Note: Router-level dependencies don't inject values into handlers. If you need the user object, add the dependency to the individual route.

## How Sessions Work

When a user logs in via `/api/v1/auth/login`:

1. FastroAI validates credentials
2. Creates a session record in Redis (or your configured backend)
3. Generates a CSRF token
4. Sets `session_id` and `csrf_token` cookies

On subsequent requests, the session dependency:

1. Reads `session_id` from cookies
2. Validates it exists in the backend and hasn't expired
3. Validates CSRF token on mutating requests (POST, PUT, DELETE, PATCH)
4. Returns the user

## CSRF Protection

Session auth includes CSRF protection by default. For non-GET requests, include the CSRF token via:

- The `csrf_token` cookie (automatically sent by browsers), or
- The `X-CSRF-Token` header (for JavaScript clients)

```javascript
const csrfToken = getCookie('csrf_token');

fetch('/api/v1/something', {
    method: 'POST',
    headers: {
        'X-CSRF-Token': csrfToken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    credentials: 'include',  // Include cookies
});
```

Disable CSRF protection (not recommended) with `CSRF_ENABLED=false`.

## Device Tracking

Sessions capture device information from the User-Agent header:

```python
from src.infrastructure.auth.session.dependencies import get_session_from_cookie

@router.get("/my-sessions")
async def my_sessions(session_data = Depends(get_session_from_cookie)):
    return {
        "device": session_data.device_info,  # browser, os, is_mobile, etc.
        "ip": session_data.ip_address,
        "created": session_data.created_at,
    }
```

This helps detect suspicious activity or let users see their active sessions.

## Login Rate Limiting

The session system tracks failed login attempts per IP address and username. After `LOGIN_MAX_ATTEMPTS` failures within `LOGIN_WINDOW_MINUTES`, further attempts are blocked.

This happens automatically on the login endpoint.

## Session Limits

By default, users can have up to 5 concurrent sessions (`MAX_SESSIONS_PER_USER`). When a user exceeds this, the oldest session is terminated.

## Storage Backends

Sessions are stored server-side. Configure the backend:

```bash
SESSION_BACKEND=redis      # Default, recommended for production
SESSION_BACKEND=memcached  # Alternative
SESSION_BACKEND=memory     # Testing only, not for production
```

Redis is recommended because it supports key expiration, pattern scanning for cleanup, and persists across restarts.

## Configuration

```bash
SESSION_BACKEND=redis
SESSION_TIMEOUT_MINUTES=30        # Inactive sessions expire
SESSION_CLEANUP_INTERVAL_MINUTES=15
MAX_SESSIONS_PER_USER=5
SESSION_SECURE_COOKIES=true       # HTTPS only
SESSION_COOKIE_MAX_AGE=86400      # Cookie lifetime (1 day)

CSRF_ENABLED=true

LOGIN_MAX_ATTEMPTS=5
LOGIN_WINDOW_MINUTES=15
```

## Key Files

| Component | Location |
|-----------|----------|
| Dependencies | `backend/src/infrastructure/auth/session/dependencies.py` |
| Session manager | `backend/src/infrastructure/auth/session/manager.py` |
| Storage backends | `backend/src/infrastructure/auth/session/backends/` |
| Schemas | `backend/src/infrastructure/auth/session/schemas.py` |

---

[← Authentication Overview](index.md){ .md-button } [JWT Tokens →](jwt.md){ .md-button .md-button--primary }
