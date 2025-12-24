# Infrastructure

FastroAI comes with several infrastructure components that handle common concerns: caching, rate limiting, background tasks, and email. These are optional but enabled by default, and they share a common pattern: each can be toggled on/off and configured via environment variables.

## What's Included

| Component | Purpose | Backend Options |
|-----------|---------|-----------------|
| **Caching** | Store and retrieve data quickly | Redis, Memcached |
| **Rate Limiting** | Prevent abuse, enforce usage tiers | Redis, Memcached |
| **Background Tasks** | Run work outside request cycles | Redis, RabbitMQ (via Taskiq) |
| **Email** | Send transactional emails | Postmark |

All four components follow the same configuration pattern: a primary enable/disable flag, a backend selection, and backend-specific connection settings.

## Enabling and Disabling

Each component has a master switch:

```bash
CACHE_ENABLED=true
RATE_LIMITER_ENABLED=true
TASKIQ_ENABLED=true
EMAIL_ENABLED=true
```

When disabled, the component doesn't initialize at startup. For caching and rate limiting, the decorators and middleware become no-ops. For taskiq, tasks won't be processed. For email, sending attempts will be skipped.

## Backend Selection

Caching and rate limiting support multiple backends:

```bash
CACHE_BACKEND=redis          # or "memcached"
RATE_LIMITER_BACKEND=redis   # or "memcached"
TASKIQ_BROKER_TYPE=redis     # or "rabbitmq"
```

Choose Redis if you need pattern-based cache invalidation or want a single service for multiple purposes. Memcached works well for simple key-value caching where you don't need pattern matching.

## Connection Sharing

Redis is used by multiple components, but they use different databases to avoid key collisions:

| Component | Default Redis DB |
|-----------|------------------|
| Cache | 0 |
| Rate Limiter | 1 |
| Taskiq | 3 |

You can change these defaults if needed, but keeping them separate prevents one component from accidentally interfering with another.

## Initialization

All infrastructure components initialize during app startup in `backend/src/infrastructure/app_factory.py`. The startup sequence checks each component's enabled flag and only initializes what's needed. If a backend isn't available (say, Redis is down), the app logs a warning but continues starting, operating in degraded mode where applicable.

## Key Files

| Component | Location |
|-----------|----------|
| Caching | `backend/src/infrastructure/cache/` |
| Rate Limiting | `backend/src/infrastructure/rate_limit/` |
| Background Tasks | `backend/src/infrastructure/taskiq/` |
| Email | `backend/src/infrastructure/email/` + `backend/src/modules/email/` |
| Settings | `backend/src/infrastructure/config/settings.py` |

---

[← Customizing Admin](../admin/customizing.md){ .md-button } [Caching →](caching.md){ .md-button .md-button--primary }
