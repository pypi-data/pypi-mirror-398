# API Keys

API keys give users programmatic access to your API. If you're building a developer-facing product, users will need keys to integrate with your service. If you're letting users automate workflows or build on top of your platform, they'll need keys too.

## How Keys Work

FastroAI API keys look like this:

```
fai_aBcDeFgH_remainingRandomCharacters
```

The `fai_` prefix identifies it as a FastroAI key. The next 8 characters are the key prefix, which is stored in the database for identification (so you can show users "Key ending in aBcDeFgH"). The rest is the secret part.

Only a SHA-256 hash of the full key is stored. Once a user creates a key and sees it, that's it. If they lose it, they need to create a new one.

## Creating Keys

Users create their own keys through the API. They're authenticated with their session, and the key they create belongs to them:

```bash
POST /api/v1/api-keys/
Authorization: Bearer <session_token>
Content-Type: application/json

{
    "name": "Production API",
    "permissions": {
        "conversations": ["read", "write"],
        "analytics": ["read"]
    },
    "usage_limits": {
        "requests_per_day": 10000
    },
    "expires_at": "2025-12-31T23:59:59Z"
}
```

The response includes the full API key. This is the only time it's shown:

```json
{
    "id": 1,
    "name": "Production API",
    "key_prefix": "aBcDeFgH",
    "api_key": "fai_aBcDeFgH_xyz123...",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
}
```

Tell your users to save this key somewhere secure. They won't be able to see it again.

## Permissions

Each API key has permissions that control what it can do. Permissions are defined as resource + action pairs.

Resources include `conversations`, `credits`, `ai_usage`, `user_profile`, `analytics`, `admin`, `billing`, and `api_keys`. Actions include `read`, `write`, `create`, `update`, `delete`, `list`, and `admin`. You can also use `*` as a wildcard for either.

When a request comes in, the validation checks permissions in order of specificity:

1. Exact match (`resource=conversations, action=read`)
2. Resource wildcard (`resource=*, action=read`)
3. Action wildcard (`resource=conversations, action=*`)
4. Full wildcard (`resource=*, action=*`)

So you can create narrow keys for specific integrations (`conversations/read` only) or broad keys for trusted applications (`*/*`).

## Key Types

Keys can have different types depending on their intended use:

- **`public`** - Read-only access, meant for client-side use where the key might be visible
- **`private`** - Full access to the user's own data, for server-side integrations
- **`admin`** - Administrative access, only for superusers
- **`service`** - For internal service-to-service communication
- **`webhook`** - For authenticating incoming webhooks

The type is informational and helps you categorize keys. The actual access control comes from the permissions.

## Validating Keys

When a request arrives with an API key, validate it before processing:

```python
from src.modules.api_keys.service import APIKeyService

api_key_service = APIKeyService()

validation = await api_key_service.validate_api_key(
    api_key="fai_aBcDeFgH_...",
    resource="conversations",
    action="read",
    db=db,
)

if validation.is_valid:
    # Key is good - process the request as validation.user_id
    user_id = validation.user_id
else:
    # Key is invalid, expired, or doesn't have permission
    # validation.error_message tells you why
    raise HTTPException(status_code=401, detail=validation.error_message)
```

The validation checks that the key exists, is active, hasn't expired, and has permission for the requested resource/action. It also updates the `last_used_at` timestamp on the key.

## Usage Tracking

Every API call made with a key can be tracked. This gives you analytics, helps with billing, and creates an audit trail:

```python
await api_key_service.record_usage(
    api_key_id=key_id,
    user_id=user_id,
    usage_data=KeyUsageCreate(
        api_key_id=key_id,
        user_id=user_id,
        endpoint="/api/v1/conversations",
        method="POST",
        status_code=200,
        tokens_used=1500,
        cost_microcents=45000,
        response_time_ms=250,
    ),
    db=db,
)
```

Users can see their key analytics through the API:

```bash
GET /api/v1/api-keys/{key_id}/analytics?days=30
```

This returns total requests, success/failure counts, token usage, costs, most-used endpoints, and error breakdowns. Useful for developers debugging their integrations or checking their usage.

## Per-Key Rate Limits

You can store rate limits on each key:

```json
{
    "requests_per_minute": 60,
    "requests_per_day": 10000,
    "tokens_per_day": 100000
}
```

These limits are stored in `usage_limits` and returned during validation. FastroAI doesn't enforce them automatically though. You'll need to implement rate limiting middleware that checks `validation.usage_limits` and tracks usage. The limits are just metadata that your middleware can use.

## Managing Keys

Users manage their own keys through these endpoints (all require session auth):

| Endpoint | What it does |
|----------|--------------|
| `POST /api/v1/api-keys/` | Create a new key |
| `GET /api/v1/api-keys/` | List all keys |
| `GET /api/v1/api-keys/{id}` | Get key details |
| `PATCH /api/v1/api-keys/{id}` | Update name, permissions, limits |
| `DELETE /api/v1/api-keys/{id}` | Deactivate key |
| `GET /api/v1/api-keys/{id}/usage` | Usage history |
| `GET /api/v1/api-keys/{id}/analytics` | Usage analytics |
| `GET /api/v1/api-keys/summary/user` | Summary of all keys |

When a key is "deleted," it's actually deactivated. The record stays in the database for audit purposes, but the key won't validate anymore.

## Security Notes

Keys are hashed with SHA-256 before storage, so even if someone gets database access, they can't recover the actual keys. Each key tracks when it was last used and from what IP address, which helps detect suspicious activity. Keys can have expiration dates, and once deactivated, they can't be reactivated through the API (you'd need to create a new one).

## Key Files

| Component | Location |
|-----------|----------|
| API key service | `backend/src/modules/api_keys/service.py` |
| Permission enums | `backend/src/modules/api_keys/enums.py` |
| Key models | `backend/src/modules/api_keys/models.py` |
| API endpoints | `backend/src/interfaces/api/v1/api_keys.py` |

---

[← Entitlements](entitlements.md){ .md-button } [Payments →](../payments/index.md){ .md-button .md-button--primary }
