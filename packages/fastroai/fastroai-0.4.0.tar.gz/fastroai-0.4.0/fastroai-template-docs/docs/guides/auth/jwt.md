# JWT Tokens

JWT (JSON Web Tokens) provide stateless authentication. They're useful when cookies aren't an option, like mobile apps, external API clients, or third-party integrations.

Keep in mind that FastroAI's built-in routes use [sessions](sessions.md) by default. JWT dependencies are there when you need them for specific use cases.

## Protecting Routes

To protect a route with JWT authentication, import the dependencies:

```python
from fastapi import APIRouter, Depends

from src.infrastructure.auth.jwt.dependencies import get_current_user

router = APIRouter()

@router.get("/mobile/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["id"]}
```

The dependency validates the `Authorization: Bearer <token>` header and extracts the user.

### Available Dependencies

The JWT dependencies mirror the session ones, but validate tokens instead of session cookies:

**`get_current_user`** returns the authenticated user. If the token is invalid or missing, it raises 401.

```python
@router.get("/dashboard")
async def dashboard(current_user: dict = Depends(get_current_user)):
    return {"welcome": current_user["username"]}
```

**`get_current_superuser`** works the same way, but also checks `is_superuser=True`. Raises 403 if the user isn't a superuser.

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_superuser),
):
    # Only superusers reach this code
    ...
```

**`get_optional_user`** returns the user if authenticated, `None` otherwise. It never raises an exception, so you can use it for routes that work differently for logged-in vs anonymous users.

```python
@router.get("/products")
async def list_products(current_user: dict | None = Depends(get_optional_user)):
    if current_user:
        # Show personalized products
        ...
```

## How JWT Works

JWT tokens are self-contained, meaning the server doesn't store them anywhere. When a user authenticates, the server:

1. Signs the token with `SECRET_KEY` on creation
2. Verifies the signature on each request
3. Checks the expiration claim

There's no database lookup per request (except to fetch user data after validation). This makes JWT great for distributed systems where you don't want to hit a central session store on every request.

## Token Types

FastroAI issues two token types with different lifetimes and purposes:

**Access Token** is short-lived (30 minutes by default). You include it in API requests to prove who you are.

**Refresh Token** is long-lived (7 days by default). When the access token expires, you use this to get a new one without making the user log in again.

The login endpoint returns both:

```json
{
    "access_token": "eyJ...",
    "token_type": "bearer"
}
```

The refresh token is set as an HTTP-only cookie for security.

## Getting Tokens

To get tokens, hit the login endpoint with credentials:

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secret
```

You'll get the access token in the response body and the refresh token in a cookie.

When the access token expires, refresh it:

```bash
POST /api/v1/auth/refresh
Cookie: refresh_token=...
```

This returns a fresh access token.

## Using Tokens

Include the access token in the Authorization header:

```bash
GET /api/v1/some-endpoint
Authorization: Bearer eyJ...
```

In JavaScript:

```javascript
fetch('/api/v1/some-endpoint', {
    headers: {
        'Authorization': `Bearer ${accessToken}`,
    },
});
```

## Token Expiration

| Token | Default | Setting |
|-------|---------|---------|
| Access | 30 minutes | `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Refresh | 7 days | `REFRESH_TOKEN_EXPIRE_DAYS` |

When the access token expires, use the refresh token to get a new one. When the refresh token expires, the user needs to log in again.

For most apps, these defaults work well. Shorter access tokens mean less exposure if one gets compromised. Longer refresh tokens mean fewer re-logins.

## Custom Token Claims

If you need to add extra data to tokens (like roles or tenant IDs), modify `create_access_token` in `security.py`:

```python
# In create_access_token(), add to the payload:
to_encode = {
    "sub": data["sub"],
    "username_or_email": data.get("username_or_email"),
    "roles": data.get("roles", []),  # Custom claim
    "token_type": "access",
    "exp": expire,
}
```

Then update the dependency to extract and use those claims. Any data you put in the token is available on every request without a database lookup.

## Configuration

JWT settings are read from your `backend/.env` file:

```bash
SECRET_KEY=your-production-secret-here  # MUST change in production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

The `SECRET_KEY` is critical. Anyone with it can forge valid tokens. Generate a secure one:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## When to Use JWT vs Sessions

| Scenario | Use |
|----------|-----|
| Web app with cookies | Sessions |
| SPA with cookie support | Sessions |
| Mobile app | JWT |
| Third-party API integration | JWT or API Keys |
| Microservice-to-microservice | JWT |

Sessions give you more control: CSRF protection, device tracking, and the ability to invalidate sessions server-side. JWT is simpler when you can't use cookies, but you lose those features.

If you're building a web app and wondering which to pick, start with sessions. You can always add JWT endpoints later for specific use cases.

## Key Files

| Component | Location |
|-----------|----------|
| Dependencies | `backend/src/infrastructure/auth/jwt/dependencies.py` |
| Token creation | `backend/src/infrastructure/auth/jwt/security.py` |
| Token schemas | `backend/src/infrastructure/auth/jwt/schemas.py` |
| JWT router | `backend/src/infrastructure/auth/jwt/router.py` |

---

[← Sessions](sessions.md){ .md-button } [OAuth Providers →](oauth-providers.md){ .md-button .md-button--primary }
