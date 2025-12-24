# Customizing Features

**Start minimal. Add complexity only when you need it.**

FastroAI comes with everything - payments, background tasks, caching, monitoring. That's great when you need it all. But what if you're building an internal tool? Or a prototype? Or you just want to understand how things work without the noise?

This guide shows you how to disable or remove features you don't need. Every removal is reversible, so you can experiment freely.

## Why Remove Features?

FastroAI ships with everything, but you probably don't need everything. Here's when you might want to strip things down:

**You're prototyping.** Why worry about Stripe integration when you're just testing if your idea works? Turn it off and focus on the core functionality.

**You're building an internal tool.** Your team dashboard doesn't need payment processing. Why deal with that complexity?

**You want to understand the code.** It's way easier to learn FastAPI patterns when you're not also trying to figure out Taskiq workers and Redis caching.

**You're watching costs.** Every Redis instance costs money. Every background worker costs money. Don't pay for what you don't use.

**You're tightening security.** Less code running means fewer things that can break. Removing the admin panel in production? Smart move.

## The Smart Way to Remove Features

Here's the thing - you don't always need to delete code. FastroAI is designed to let you disable features through configuration. Try that first.

The process is always the same:

1. **Try disabling via .env first** - Often just one line
2. **Test that everything still works** - Run the app, check the endpoints
3. **Remove the code if needed** - Only if you want a cleaner codebase

Most people stop at step 1. The code stays there, ready to re-enable when you need it.

## Quick Disable Examples

Need to turn something off? Here are the one-line changes that disable major features:

### Turn Off Caching and Rate Limiting

Building a prototype? Don't want to deal with Redis right now?

```env
# backend/.env
CACHE_ENABLED=false
RATE_LIMITER_ENABLED=false
```

Done. FastroAI skips Redis entirely. Rate limiting falls back to memory (which works fine if you're running a single process and not expecting thousands of users).

### Disable Background Tasks

Taskiq is powerful but complex. If you're just building a simple app and don't need background tasks:

```env
TASKIQ_ENABLED=false
```

The workers won't start. You'll need to update any code that queues tasks to call services directly, but the app runs fine without background task processing.


### Remove Admin Panel

The admin panel is handy but also creates another attack surface:

```env
ADMIN_ENABLED=false
```

Poof. The `/admin` endpoint disappears.

### Disable Monitoring

Logfire is awesome for production but can be noisy when you're just trying to build:

```env
LOGFIRE_ENABLED=false
```

No more traces cluttering your console. Pure, clean logs.

### Turn Off Stripe

Not ready to charge money? Skip the payment complexity:

```env
STRIPE_ENABLED=false
```

The payment endpoints stay there but return appropriate errors. Build your app first, worry about money later.

## Complete Feature Removal

Sometimes you want to actually remove code, not just disable it. Maybe you're building a minimal Docker image, or you want a cleaner codebase for learning. Here's how to do it properly:

<div class="grid cards" markdown>

-   :material-database-off: **Remove Redis**

    ---
    
    Eliminate caching, rate limiting, and Redis sessions entirely.
    
    [Jump to Redis removal →](#removing-redis-cache-rate-limiting)

-   :material-cog-off: **Remove Taskiq**

    ---
    
    Strip out background tasks and workers for simpler architecture.
    
    [Jump to Taskiq removal →](#removing-taskiq-background-tasks)

-   :material-credit-card-off: **Remove Stripe**

    ---
    
    Delete payment processing when you don't need to charge money.
    
    [Jump to Stripe removal →](#removing-stripe-payments)

</div>

### Removing Redis (Cache + Rate Limiting)

Redis is used for caching, rate limiting, and session storage. Here's how to remove it completely:

**Step 1: Disable in configuration**
```env
CACHE_ENABLED=false
RATE_LIMITER_ENABLED=false
SESSION_BACKEND=memory  # Switch from redis to memory
```

**Step 2: Remove from Docker Compose**
```yaml
# docker-compose.yml - comment out or delete
# redis:
#   image: redis:7-alpine
#   ports:
#     - "6379:6379"
#   volumes:
#     - redis_data:/data
```

**Step 3: Remove dependencies (optional)**
```toml
# pyproject.toml - remove these lines
# "redis>=5.0.0",
# "hiredis>=2.2.0",
```

Then reinstall:
```bash
uv pip install -e ".[dev]"
```

Rate limiting switches to in-memory (single process only). Caching gets disabled completely. Sessions use memory storage instead of Redis.

### Removing Taskiq (Background Tasks)

Taskiq handles async background tasks - email sending, notifications, etc. You might prefer synchronous operation for simpler architecture.

**Step 1: Replace async task calls with direct calls**

Find where tasks are called:
```bash
grep -r "\.kiq(" backend/src/
```

Replace async task calls:
```python
# Before (async with Taskiq)
from modules.email.tasks import send_email_task
await send_email_task.kiq(
    recipient_email=user_email,
    subject=subject,
    template_name="welcome",
    template_vars={"user_name": user.name}
)

# After (synchronous)
from modules.email.service import EmailService
email_service = EmailService()
await email_service.send_email(
    recipient=user_email,
    subject=subject,
    template_name="welcome",
    template_vars={"user_name": user.name}
)
```

**Step 2: Remove Taskiq services**
```yaml
# docker-compose.yml - comment out
# taskiq-worker:
#   command: python -m taskiq worker src.infrastructure.taskiq.worker:email_broker
```

**Step 3: Disable Taskiq in settings**
```env
# backend/.env
TASKIQ_ENABLED=false
```

**Step 4: Delete Taskiq code (optional)**
```bash
rm -rf backend/src/infrastructure/taskiq/
rm -rf backend/src/modules/email/tasks.py
```

Email sending becomes synchronous (might slow down requests). No background job processing. Much simpler architecture overall.

### Removing Stripe (Payments)

This is the most complex removal because payments touch many parts of the system.

**Step 1: Disable Stripe endpoints**
```python
# backend/src/interfaces/api/v1/__init__.py
# Comment out these lines
# from .payments import router as payments_router
# router.include_router(payments_router, prefix="/payments")
```

**Step 2: Handle entitlement dependencies**

The entitlement system works without Stripe, but you might want to simplify it:
```python
# In any code that checks entitlements
if not settings.STRIPE_ENABLED:
    # Everyone gets full access in dev
    return True
```

**Step 3: Remove Stripe dependencies**
```toml
# pyproject.toml
# "stripe>=7.0.0",
```

Payment endpoints disappear completely. You'll need alternative logic for entitlements. Subscriptions won't work anymore.

## Building a Minimal FastroAI

Want the absolute minimum? Here's a configuration with just auth, database, and AI:

### Minimal Environment

```env
# backend/.env - Minimal setup

# Required
SECRET_KEY=<generate-with-openssl-rand-hex-32>
OPENAI_API_KEY=<your-openai-key>
ADMIN_PASSWORD=changeme

# Disabled features
CACHE_ENABLED=false
RATE_LIMITER_ENABLED=false
TASKIQ_ENABLED=false
ADMIN_ENABLED=false
LOGFIRE_ENABLED=false
STRIPE_ENABLED=false
EMAIL_ENABLED=false

# Simplified session storage
SESSION_BACKEND=memory
```

### Minimal Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: fastroai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build:
      context: .
      dockerfile: backend/Dockerfile
    command: uvicorn src.interfaces.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file:
      - backend/.env
    volumes:
      - ./backend:/app
    depends_on:
      - db

volumes:
  postgres_data:
```

Just PostgreSQL and your API. Nothing else.

This minimal setup is perfect for learning and prototyping. You get the core - authentication, AI integration, database operations - without the complexity of background workers, Redis clusters, and payment processing.

Your requests will be slower without caching, but that doesn't matter when you're the only user. You won't have fancy monitoring, but console logs work fine when you're debugging. You can't charge money yet, but you probably don't have customers anyway.

!!! tip "Start Here, Add Later"
    This minimal approach lets you understand how FastroAI actually works before adding layers of complexity. Once you know the core patterns, adding Redis or Taskiq back becomes much easier.

## Adding Features Back

Changed your mind? Need that feature after all? No problem.

### Re-enabling via Configuration

If you just disabled via `.env`:

```env
# backend/.env
CACHE_ENABLED=true  # Turn it back on
```

Restart your app. The feature is back.

### Restoring Deleted Code

If you actually deleted code:

```bash
# See when file was deleted
git log --all --full-history -- backend/src/infrastructure/taskiq/brokers.py

# Restore from that commit
git checkout abc123^ -- backend/src/infrastructure/taskiq/

# Or just restore from your last tag
git checkout full-template -- backend/src/infrastructure/taskiq/
```

Pro tip: Tag your repo before removing features:
```bash
git tag -a before-removal -m "Full template before customization"
```

### Re-adding Dependencies

If you removed packages:

```toml
# pyproject.toml - add back
"redis>=5.0.0",
"taskiq>=0.11.0",
"taskiq-redis>=1.1.0",
```

Then:
```bash
uv pip install -e ".[dev]"
```

## Common Gotchas

Here are the issues you'll probably run into and how to fix them:

**"Import errors after removing features"**

You probably have imports still pointing to removed code:
```python
# backend/src/interfaces/api/v1/__init__.py
# Comment out imports for removed features
# from .payments import router as payments_router
```

**"Rate limiting not working after removing Redis"**

Memory-based rate limiting only works per-process. With multiple workers, each has its own counter. Use Redis for production rate limiting or run single-worker.

**"Tests failing after removal"**

Skip or remove tests for disabled features:
```python
@pytest.mark.skipif(not settings.TASKIQ_ENABLED, reason="Taskiq disabled")
def test_background_task():
    pass
```

**"Database errors about missing tables"**

If you removed models, you need new migrations:
```bash
# Generate migration without removed models
docker compose exec web alembic revision --autogenerate -m "Remove payment models"
docker compose exec web alembic upgrade head
```

!!! tip "Git Safety Net"
    Tag your repo before removing features: `git tag before-removal`. You can always restore with `git checkout before-removal -- path/to/file`.

## Feature Dependency Map

Some features depend on others. Here's what breaks when you remove something:

| If you remove... | These features break... | Workaround |
|-----------------|------------------------|------------|
| **Redis** | Rate limiting (Redis-based), Session storage (Redis), Cache | Use memory backends (single-process only) |
| **Taskiq** | Email sending (async), Scheduled tasks | Make operations synchronous |
| **Stripe** | Payment processing, Subscription management | Implement custom entitlement logic |
| **Database** | Everything | You need a database |

## Production Considerations

Removing features in production needs more thought than in development:

**Rate limiting without Redis** only works with single worker. Not suitable for high traffic.

**Memory sessions** are lost on restart. Users get logged out every time you deploy.

**No monitoring** means you're flying blind. Keep Logfire in production unless you have an alternative.

**Removing admin panel** is actually recommended for production. Less attack surface.

**Synchronous email** (no Taskiq) can timeout on slow SMTP servers. Consider keeping Taskiq just for email.

!!! warning "Memory Sessions in Production"
    If you remove Redis and use memory sessions, your users will get logged out every time you deploy. This might be fine for internal tools but terrible for customer-facing apps.

## Use What You Need

You don't have to use everything. FastroAI ships with a lot of features, but that doesn't mean you need them all. Your prototype doesn't need Stripe integration. Your internal tool doesn't need rate limiting. Your learning project doesn't need background tasks.

Here's the approach that works:
1. Disable via configuration first (one line in `.env`)
2. Test everything still works  
3. Remove code only if you really want a cleaner codebase

Most of the time, step 1 is enough. The code stays there, dormant, ready to wake up when you flip the switch back.

And hey - every removal is reversible. Tag your git repo before you start chopping features. You can always go back when you realize you actually needed that admin panel.

---

**Take what you need, leave what you don't.** FastroAI works however you want to use it.

<div style="text-align: center; margin-top: 50px;">
    <a href="../../learn/" class="md-button md-button--primary">
        Next: Learn AI Development →
    </a>
</div>