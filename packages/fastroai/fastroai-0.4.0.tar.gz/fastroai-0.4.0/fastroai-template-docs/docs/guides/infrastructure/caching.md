# Caching

Caching stores frequently accessed data in memory so you don't hit the database on every request. FastroAI provides a `@cache` decorator for FastAPI endpoints and a provider API for direct cache operations.

## Configuration

Set your backend and connection details in your environment:

```bash
CACHE_ENABLED=true
CACHE_BACKEND=memcached                # or "redis"
DEFAULT_CACHE_EXPIRATION=3600          # seconds

# Redis connection
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0
CACHE_REDIS_PASSWORD=                  # leave empty if none
CACHE_REDIS_POOL_SIZE=10

# Memcached connection (if using memcached)
CACHE_MEMCACHED_HOST=localhost
CACHE_MEMCACHED_PORT=11211
CACHE_MEMCACHED_POOL_SIZE=10
```

## The Cache Decorator

The `@cache` decorator handles caching for GET endpoints and invalidation for mutations:

```python
from infrastructure.cache import cache

@app.get("/users/{user_id}")
@cache(key_prefix="user", resource_id_name="user_id", expiration=600)
async def get_user(request: Request, user_id: int):
    # This result gets cached for 600 seconds
    return await user_service.get(user_id)

@app.put("/users/{user_id}")
@cache(key_prefix="user", resource_id_name="user_id")
async def update_user(request: Request, user_id: int, data: UserUpdate):
    # PUT/POST/DELETE automatically invalidate the cache key
    return await user_service.update(user_id, data)
```

The decorator builds cache keys from the prefix and resource ID: `user:123`. On GET requests, it checks the cache first and returns cached data if available. On mutations (PUT, POST, DELETE), it invalidates the key after the operation succeeds.

### Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key_prefix` | str | Unique identifier for this cache type (required) |
| `resource_id_name` | str | Function argument containing the ID (auto-detected if not specified) |
| `expiration` | int | TTL in seconds (default: 3600) |
| `resource_id_type` | type | Expected ID type: `int`, `str`, or tuple (default: `int`) |
| `to_invalidate_extra` | dict | Additional cache keys to invalidate on mutations |
| `pattern_to_invalidate_extra` | list | Key patterns to invalidate (Redis only) |

### Invalidating Related Keys

When updating a resource, you often need to invalidate related caches. Use `to_invalidate_extra`:

```python
@app.put("/posts/{post_id}")
@cache(
    key_prefix="post",
    to_invalidate_extra={"user_posts": "author_id"}  # Also invalidate user_posts:{author_id}
)
async def update_post(request: Request, post_id: int, author_id: int, data: PostUpdate):
    return await post_service.update(post_id, data)
```

For bulk invalidation with patterns (Redis only):

```python
@app.delete("/users/{user_id}")
@cache(
    key_prefix="user",
    pattern_to_invalidate_extra=["user:{user_id}:*"]  # Invalidate all user sub-keys
)
async def delete_user(request: Request, user_id: int):
    return await user_service.delete(user_id)
```

## Direct Cache Operations

For more control, use the cache provider directly:

```python
from infrastructure.cache import get, set, delete, delete_pattern, exists, clear

# Store a value
await set(key="config:site_name", value="My App", expiration=3600)

# Retrieve it
value = await get(key="config:site_name")

# Check existence
if await exists(key="config:site_name"):
    ...

# Delete single key
await delete(key="config:site_name")

# Delete by pattern (Redis only)
await delete_pattern(pattern="user:123:*")

# Clear everything
await clear()
```

Values are automatically JSON serialized, so you can store dictionaries, lists, and other JSON-compatible types.

## Redis vs Memcached

Both backends work with the decorator and provider API, but they have different capabilities:

| Feature | Redis | Memcached |
|---------|-------|-----------|
| Pattern-based deletion | Yes | No |
| Data persistence | Optional | No |
| Data structures | Rich (lists, sets, hashes) | Key-value only |
| Memory efficiency | Good | Excellent |

If you need `delete_pattern()` or `pattern_to_invalidate_extra`, you need Redis. Memcached raises `PatternMatchingNotSupportedError` when you try pattern operations.

## Graceful Degradation

If the cache backend becomes unavailable, the decorator catches the error and falls through to the underlying function. Your endpoint keeps working, it's slower because it hits the database, but it doesn't crash. This fail-open behavior is intentional since cached data is typically reproducible from the source.

## Key Files

| Component | Location |
|-----------|----------|
| Decorator | `backend/src/infrastructure/cache/decorator.py` |
| Provider API | `backend/src/infrastructure/cache/provider.py` |
| Redis backend | `backend/src/infrastructure/cache/backends/redis.py` |
| Memcached backend | `backend/src/infrastructure/cache/backends/memcached.py` |
| Settings | `backend/src/infrastructure/config/settings.py:75-124` |

---

[← Infrastructure Overview](index.md){ .md-button } [Rate Limiting →](rate-limiting.md){ .md-button .md-button--primary }
