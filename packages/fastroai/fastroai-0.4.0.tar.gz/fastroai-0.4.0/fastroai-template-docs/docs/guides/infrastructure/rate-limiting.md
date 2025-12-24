# Rate Limiting

Rate limiting prevents abuse and enforces usage tiers. FastroAI's rate limiter works at two levels: a global middleware that applies default limits to all requests, and per-tier limits stored in the database that let you differentiate between user tiers.

## How It Works

Every request goes through the rate limit middleware. The middleware identifies the requester (user ID if authenticated, IP address if not), looks up any tier-specific limits, and checks whether they've exceeded their quota. If they have, the request gets a 429 response. If not, it proceeds and the counter increments.

```
Request → Identify User/IP → Look Up Tier Limits → Check Counter → Allow or Block
```

Authenticated users get their limits from the `rate_limits` table based on their tier. Anonymous users always get the system defaults.

## Configuration

```bash
RATE_LIMITER_ENABLED=true
RATE_LIMITER_BACKEND=memcached          # or "redis"
RATE_LIMITER_FAIL_OPEN=true             # allow requests if backend unavailable

DEFAULT_RATE_LIMIT_LIMIT=100            # requests allowed
DEFAULT_RATE_LIMIT_PERIOD=60            # time window in seconds

# Redis connection
RATE_LIMITER_REDIS_HOST=localhost
RATE_LIMITER_REDIS_PORT=6379
RATE_LIMITER_REDIS_DB=1                 # different from cache DB
RATE_LIMITER_REDIS_PASSWORD=
RATE_LIMITER_REDIS_POOL_SIZE=10

# Memcached connection (if using memcached)
RATE_LIMITER_MEMCACHED_HOST=localhost
RATE_LIMITER_MEMCACHED_PORT=11211
RATE_LIMITER_MEMCACHED_POOL_SIZE=10
```

The default settings allow 100 requests per minute per user/IP. Adjust these based on your API's capacity and expected usage patterns.

## Per-Tier Limits

The real power comes from tier-based limits stored in the database. The `rate_limits` table lets you define different limits for different subscription tiers and endpoints:

```python
# In admin or via service
await crud_rate_limits.create(
    db=db,
    object={
        "tier_id": premium_tier.id,
        "path": "/api/v1/conversation",
        "name": "conversation_premium",
        "limit": 1000,
        "period": 3600
    }
)
```

This gives premium tier users 1000 requests per hour to the conversation endpoint, while other tiers fall back to the system defaults.

The middleware checks for tier-specific limits first. If none exist for the user's tier and the requested path, it uses `DEFAULT_RATE_LIMIT_LIMIT` and `DEFAULT_RATE_LIMIT_PERIOD`.

### The RateLimit Model

| Field | Type | Description |
|-------|------|-------------|
| `tier_id` | int | Foreign key to tiers table |
| `path` | str | API path like `/api/v1/users` |
| `name` | str | Descriptive name for this rule |
| `limit` | int | Maximum requests allowed |
| `period` | int | Time window in seconds |

## Response Headers

Every response includes rate limit headers so clients can track their usage:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 60
```

When a request is rate limited, the response is:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
Content-Type: application/json

{"detail": "Rate limit exceeded. Try again in 60 seconds."}
```

## Fail-Open vs Fail-Closed

The `RATE_LIMITER_FAIL_OPEN` setting controls what happens when the backend (Redis/Memcached) is unavailable:

**Fail-Open (default: true)**: Requests are allowed through when the backend is down. This prioritizes availability, your API stays up even if rate limiting temporarily stops working.

**Fail-Closed (false)**: Requests are blocked when the backend is down. This prioritizes security, no one gets through without proper rate limit checks.

For most APIs, fail-open makes sense. For security-critical endpoints where you absolutely need rate limiting (like login attempts), consider fail-closed.

## Per-Endpoint Dependencies

Beyond the global middleware, you can explicitly require rate limiting on specific endpoints using the dependency:

```python
from interfaces.api.dependencies import RateLimited

@router.get("/expensive-operation")
async def expensive_operation(
    _: RateLimited,
    db: DbSession = Depends(async_session),
):
    return await do_expensive_thing(db)
```

This adds an explicit rate limit check. It's useful for endpoints that need stricter enforcement or different behavior than the middleware provides.

## Anonymous vs Authenticated

The middleware uses different identifiers depending on authentication status:

| User Type | Identifier | Limit Source |
|-----------|------------|--------------|
| Authenticated | User ID | Tier-specific or system default |
| Anonymous | Client IP | System default only |

Authenticated users benefit from tier-based limits. Anonymous users always get the default limits and share a rate limit pool per IP address.

## Key Files

| Component | Location |
|-----------|----------|
| Middleware | `backend/src/infrastructure/rate_limit/middleware.py` |
| Provider API | `backend/src/infrastructure/rate_limit/provider.py` |
| RateLimit model | `backend/src/modules/rate_limit/models.py` |
| Settings | `backend/src/infrastructure/config/settings.py:126-172` |
| API dependency | `backend/src/interfaces/api/dependencies.py:36` |

---

[← Caching](caching.md){ .md-button } [Background Tasks →](background-tasks.md){ .md-button .md-button--primary }
