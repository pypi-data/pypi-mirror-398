# Logging & Tracing

FastroAI provides a centralized logging system through `get_logger()`. It auto-detects module names, supports correlation IDs for request tracing, and outputs in different formats depending on your environment.

## Getting a Logger

Call `get_logger()` without arguments and it figures out the calling module's name for you:

```python
from infrastructure.logging import get_logger

logger = get_logger()
logger.info("Application started")
logger.error("Something went wrong", extra={"error_code": 500})
```

If you want a specific name or need to add context that shows up in every log entry from that logger:

```python
# Explicit name
logger = get_logger("my.custom.logger")

# With extra context - creates a LoggerAdapter
logger = get_logger(service="payment", version="1.0")
logger.info("Processing payment")  # service and version included automatically
```

## Log Levels

Standard Python logging levels:

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed diagnostic information |
| `INFO` | General operational events |
| `WARNING` | Something unexpected but not breaking |
| `ERROR` | Something failed |
| `CRITICAL` | Application-level failure |

Set the level via `LOG_LEVEL` in your environment. In production, WARNING is a good choice to cut down on noise.

## Output Formats

Four formats are available via `LOG_FORMAT`:

**simple** - Minimal, good for quick debugging:
```
[INFO] module_name: message
```

**detailed** - Adds timestamps:
```
2024-12-02 15:30:45 [    INFO] module_name: message
```

**structured** - Key-value pairs that log aggregators can parse:
```
timestamp=2024-12-02T15:30:45.123Z level=INFO module=fastroai.chat message="Processing started" user_id=123
```

**json** - Full JSON for machine consumption:
```json
{"timestamp": "2024-12-02T15:30:45.123Z", "level": "INFO", "module": "fastroai.chat", "message": "Processing started", "user_id": 123}
```

Development defaults to detailed with colors. Production defaults to JSON so your log aggregation tools can parse it.

## Correlation IDs

Correlation IDs let you trace a single request across multiple log entries. When `LOG_CORRELATION_ID=true`, the logging system can attach an ID to every log record from that request.

The easiest way is to get a logger with a specific correlation ID:

```python
from infrastructure.logging import get_logger_with_correlation_id

logger = get_logger_with_correlation_id("req-abc123")
logger.info("Processing request")   # correlation_id included
logger.info("Request complete")     # same correlation_id
```

You can also manage correlation IDs directly if you need more control:

```python
from infrastructure.logging.config import (
    generate_correlation_id,
    set_correlation_id,
    get_correlation_id,
)

# Generate a new ID (returns a UUID string)
correlation_id = generate_correlation_id()

# Set it for the current async context
set_correlation_id(correlation_id)

# Retrieve it later
current_id = get_correlation_id()
```

The system checks several places for correlation IDs: context variables, thread local storage, request headers (`x-correlation-id`, `x-request-id`), and the request state object.

## Child Loggers

For complex services with multiple components, you can create child loggers that inherit from a parent but add their own context:

```python
from infrastructure.logging import get_logger, create_child_logger

parent = get_logger()
auth_logger = create_child_logger(parent, "auth", component="oauth")
auth_logger.info("Login successful")  # includes component="oauth"
```

## File Logging

Enable file logging with automatic rotation:

```bash
LOG_FILE_ENABLED=true
LOG_FILE_PATH=logs/fastroai.log
LOG_FILE_MAX_SIZE=10485760    # 10MB
LOG_FILE_BACKUP_COUNT=5       # Keep 5 rotated files
```

When a log file hits `LOG_FILE_MAX_SIZE`, it gets renamed with a numeric suffix and a new file starts. After `LOG_FILE_BACKUP_COUNT` rotations, the oldest file gets deleted.

## AI Execution Tracing

For AI operations, there's a dedicated `ExecutionTracer` that tracks timing, metrics, and errors:

```python
from infrastructure.ai.observability import ExecutionTracer

tracer = ExecutionTracer()

async with tracer.trace_execution("ai_response", user_id=user_id, model="gpt-4o") as trace_id:
    response = await generate_response(prompt)
    tracer.add_metric(trace_id, "response_tokens", len(response))
    return response
```

The tracer gives you methods for AI-specific logging:

| Method | Purpose |
|--------|---------|
| `trace_execution()` | Context manager for timing operations |
| `add_metric()` | Record custom metrics |
| `log_usage()` | Log token usage |
| `log_tool_execution()` | Log tool calls |
| `log_error()` | Log errors with trace correlation |

## Logfire Integration

When Logfire is enabled, logs get forwarded to the Logfire platform. The integration handles log level mapping, extracts extra fields, and gracefully degrades if Logfire isn't reachable.

You can check if Logfire is available before using Logfire-specific features:

```python
from infrastructure.observability.logfire_config import is_logfire_available

if is_logfire_available():
    # Logfire-specific code
    pass
```

## Suppressing Noisy Loggers

In production, FastroAI automatically sets these third-party loggers to WARNING level to reduce noise:

- `urllib3.connectionpool`
- `asyncpg`
- `sqlalchemy`
- `redis`
- `aiomcache`

You'll still see warnings and errors from them, but not the routine info messages about connections and queries.

## Key Files

| Component | Location |
|-----------|----------|
| Logger factory | `backend/src/infrastructure/logging/factory.py` |
| Configuration | `backend/src/infrastructure/logging/config.py` |
| Formatters | `backend/src/infrastructure/logging/formatters.py` |
| Handlers | `backend/src/infrastructure/logging/handlers.py` |
| AI tracing | `backend/src/infrastructure/ai/observability/tracing.py` |

---

[← Observability Overview](index.md){ .md-button }
