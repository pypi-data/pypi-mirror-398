# Observability

FastroAI comes with logging and observability built around Logfire. You get structured logs out of the box, automatic instrumentation of database queries and HTTP requests, and correlation IDs for tracing requests across your system.

## What Gets Instrumented

When Logfire is enabled, FastroAI automatically instruments several components. You don't need to add any code - it happens during app startup:

| Component | What's Traced |
|-----------|---------------|
| **FastAPI** | HTTP requests/responses, route handling, middleware, exceptions |
| **SQLAlchemy** | SQL queries, parameters, transaction lifecycle, connection pool |
| **Redis** | Commands, connections, pipeline operations |
| **Pydantic AI** | Model requests/responses, token usage |
| **System Metrics** | CPU utilization, memory, swap usage |

You can toggle each instrumentation independently if you don't need all of them.

## Configuration

There are two configuration areas: Logfire settings for the observability platform and logging settings for log output.

### Logfire Settings

Enable Logfire and configure your credentials. You'll get the token from the Logfire dashboard after creating a project:

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your-logfire-token
LOGFIRE_PROJECT_NAME=your-project
LOGFIRE_SERVICE_NAME=fastroai
LOGFIRE_SERVICE_VERSION=0.1.0
LOGFIRE_ENVIRONMENT=production
```

Each instrumentation can be toggled independently. If you're not using Redis, for example, turn off that instrumentation to avoid noise:

```bash
LOGFIRE_INSTRUMENT_FASTAPI=true
LOGFIRE_INSTRUMENT_SQLALCHEMY=true
LOGFIRE_INSTRUMENT_REDIS=true
LOGFIRE_INSTRUMENT_PYDANTIC_AI=true
LOGFIRE_INSTRUMENT_SYSTEM_METRICS=true
```

Control where Logfire sends data. In development, you might want console output instead of sending to the remote service:

```bash
LOGFIRE_SEND_TO_LOGFIRE=true
LOGFIRE_CONSOLE=false
```

### Logging Settings

Set the log level and output format. The format affects how logs appear in the console and files:

```bash
LOG_LEVEL=INFO
LOG_FORMAT=structured
```

Configure where logs go. Console is on by default, file logging is off:

```bash
LOG_CONSOLE_ENABLED=true
LOG_FILE_ENABLED=false
LOG_FILE_PATH=logs/fastroai.log
LOG_FILE_MAX_SIZE=10485760
LOG_FILE_BACKUP_COUNT=5
```

Feature toggles for logging behavior. Correlation IDs help trace requests, SQL query logging is verbose so it's off by default:

```bash
LOG_CORRELATION_ID=true
LOG_LOGFIRE_INTEGRATION=true
LOG_SQL_QUERIES=false
```

Environment-specific behavior. These adjust logging based on whether you're developing or running in production:

```bash
LOG_DEVELOPMENT_VERBOSE=true
LOG_PRODUCTION_OPTIMIZE=true
```

## Environment-Specific Behavior

The logging system adjusts based on your environment. You don't need to reconfigure everything when deploying - it picks sensible defaults.

**Development** gets colored console output for readability, DEBUG level logging if `LOG_DEVELOPMENT_VERBOSE=true`, and a human-friendly format.

**Staging** uses structured output that's still readable but machine-parseable, enables file logging, and turns on Logfire so you can test your observability setup before production.

**Production** switches to JSON output for log aggregation tools, enables file rotation, and bumps the level to WARNING if `LOG_PRODUCTION_OPTIMIZE=true`. It also suppresses chatty third-party loggers (urllib3, asyncpg, sqlalchemy, redis) to WARNING level so your logs aren't flooded with routine connection messages.

## Initialization Order

Observability initializes in two stages during app startup. This matters because some instrumentations need to patch libraries before they're used:

1. **Early instrumentation** runs first, before any service clients are created. This patches Redis and Pydantic AI globally.
2. **Full instrumentation** runs after database and cache initialization. This sets up SQLAlchemy tracing and system metrics collection.

If you're adding custom instrumentation, follow this pattern - patch before you create clients.

## Key Files

| Component | Location |
|-----------|----------|
| Logfire config | `backend/src/infrastructure/observability/logfire_config.py` |
| Instrumentation | `backend/src/infrastructure/observability/instrumentation.py` |
| Logging factory | `backend/src/infrastructure/logging/factory.py` |
| Logging config | `backend/src/infrastructure/logging/config.py` |
| Settings | `backend/src/infrastructure/config/settings.py` |

---

[← Email](../infrastructure/email.md){ .md-button } [Logging & Tracing →](logging-tracing.md){ .md-button .md-button--primary }
