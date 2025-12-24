# Background Tasks

Background tasks let you run work outside the request-response cycle. Instead of making users wait for slow operations like sending emails or processing reports, you queue the work and return immediately. FastroAI uses Taskiq for this, with Redis or RabbitMQ as the message broker.

## How It Works

You define tasks as async functions decorated with `@broker.task`. When you want to run a task, you call `.kiq()` on it with the arguments. This puts a message on the queue and returns immediately. A separate worker process picks up the message and executes the task.

```
Web Request → Enqueue Task → Return Response
                   ↓
              Worker Process → Execute Task
```

The web server and workers are separate processes. Workers can run on the same machine or different machines, and you can scale them independently.

## Configuration

Enable background tasks and choose your broker:

```bash
TASKIQ_ENABLED=true
TASKIQ_BROKER_TYPE=redis    # or "rabbitmq"
```

### Redis Broker

Redis is the default and works well for most applications. It's the same Redis you might already be running for cache or rate limiting, but uses a different database number to avoid key collisions:

```bash
TASKIQ_REDIS_HOST=localhost
TASKIQ_REDIS_PORT=6379
TASKIQ_REDIS_DB=3
TASKIQ_REDIS_PASSWORD=      # leave empty if none
```

### RabbitMQ Broker

RabbitMQ is better suited for high-throughput scenarios or when you need advanced message routing. It requires installing the `taskiq-aio-pika` package:

```bash
TASKIQ_RABBITMQ_HOST=localhost
TASKIQ_RABBITMQ_PORT=5672
TASKIQ_RABBITMQ_USER=guest
TASKIQ_RABBITMQ_PASSWORD=guest
TASKIQ_RABBITMQ_VHOST=/
```

### Worker Settings

Control how many tasks workers can handle:

```bash
TASKIQ_WORKER_CONCURRENCY=2       # concurrent tasks per worker process
TASKIQ_MAX_TASKS_PER_WORKER=1000  # restart worker after this many tasks
```

The concurrency setting determines how many tasks a single worker process handles simultaneously. The max tasks setting helps prevent memory leaks by periodically recycling workers.

## Creating Tasks

Define tasks in a module under your feature. FastroAI currently uses a single broker called `email_broker` for all tasks (they're all email-related), but you can create additional brokers if needed:

```python
# backend/src/modules/myfeature/tasks.py

from infrastructure.taskiq import email_broker, register_task
from taskiq import TaskiqDepends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.taskiq.deps import get_db_session

@email_broker.task(task_name="process_report")
async def process_report_task(
    report_id: int,
    user_id: int,
    db: AsyncSession = TaskiqDepends(get_db_session),
) -> dict[str, Any]:
    """Process a report in the background."""
    report = await report_service.get(db, report_id)
    result = await heavy_processing(report)
    await report_service.update(db, report_id, {"status": "complete"})
    return {"status": "processed", "report_id": report_id}

# Register for monitoring
register_task("process_report", "email_broker", process_report_task)
```

### Key Points

1. **Task names must be unique** across all tasks on the same broker
2. **All parameters must be JSON-serializable** (except those injected with `TaskiqDepends`)
3. **Use `TaskiqDepends` for dependencies** like database sessions, they're injected at execution time
4. **Return values should be JSON-serializable** for result storage

## Enqueueing Tasks

Call `.kiq()` with the task arguments (don't pass `TaskiqDepends` parameters):

```python
# From a router or service
await process_report_task.kiq(
    report_id=123,
    user_id=456,
)
```

The call returns immediately with a task object. You can get the task ID if you need to track it:

```python
task = await process_report_task.kiq(report_id=123, user_id=456)
print(f"Queued task: {task.task_id}")
```

## Database Access in Tasks

Tasks run in a separate process from the web server, so they need their own database connections. The `get_db_session` dependency in `backend/src/infrastructure/taskiq/deps.py` creates a session for each task:

```python
from taskiq import TaskiqDepends
from infrastructure.taskiq.deps import get_db_session

@email_broker.task(task_name="my_task")
async def my_task(
    item_id: int,
    db: AsyncSession = TaskiqDepends(get_db_session),
) -> dict[str, Any]:
    # db is a fresh session for this task
    item = await crud_items.get(db=db, id=item_id)
    ...
```

The worker pool uses a connection pool configured with `NullPool` to avoid connection persistence issues across task executions.

## Running Workers

Workers are separate processes that consume from the queue. Run them with:

```bash
python -m taskiq worker src.infrastructure.taskiq.worker:email_broker --workers 2
```

In Docker, there's a dedicated service:

```yaml
taskiq-email-worker:
  command: sh -c "cd /app && python -m taskiq worker src.infrastructure.taskiq.worker:email_broker --workers 2"
  depends_on:
    - db
    - redis
```

You can run multiple workers to scale task processing. Each worker can handle multiple concurrent tasks based on the `--workers` flag.

## Built-in Email Tasks

FastroAI includes several email tasks in `backend/src/modules/email/tasks.py`:

| Task | Purpose |
|------|---------|
| `send_email_task` | Send a single email |
| `send_bulk_email_task` | Send to multiple recipients |
| `send_welcome_email_task` | Welcome emails for new users |
| `send_password_reset_email_task` | Password reset emails |
| `send_verification_email_task` | Email verification |
| `send_notification_email_task` | General notifications |
| `send_system_wide_notification_emails_task` | Broadcast to all users |

These demonstrate the patterns you'd use for your own tasks.

## Task Registry

Tasks are registered for monitoring and debugging:

```python
from infrastructure.taskiq import register_task

register_task("my_task_name", "email_broker", my_task_function)
```

The registry tracks all registered tasks and can report statistics like tasks per broker. It's optional but helpful for larger applications.

## Key Files

| Component | Location |
|-----------|----------|
| Broker setup | `backend/src/infrastructure/taskiq/brokers.py` |
| DB dependency | `backend/src/infrastructure/taskiq/deps.py` |
| Worker entry | `backend/src/infrastructure/taskiq/worker.py` |
| Task registry | `backend/src/infrastructure/taskiq/registry.py` |
| Email tasks | `backend/src/modules/email/tasks.py` |
| Settings | `backend/src/infrastructure/config/settings.py:449-485` |

---

[← Rate Limiting](rate-limiting.md){ .md-button } [Email →](email.md){ .md-button .md-button--primary }
