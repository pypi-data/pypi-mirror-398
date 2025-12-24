# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastroAI is a lightweight AI orchestration library built on PydanticAI. It provides production-ready primitives for building AI applications with automatic cost tracking, DAG-based pipelines, and distributed tracing.

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_agent.py

# Run a specific test
uv run pytest tests/test_agent.py::TestAgentConfig::test_default_values

# Type checking
uv run mypy fastroai

# Linting and formatting
uv run ruff check .
uv run ruff format .
```

## Architecture

### Core Components

**FastroAgent** (`fastroai/agent/agent.py`): Stateless wrapper around PydanticAI's Agent. Adds automatic cost calculation in microcents, distributed tracing integration, and consistent ChatResponse format. Supports both `run()` for single responses and `run_stream()` for streaming. Accepts custom PydanticAI agents via escape hatch.

**Pipeline** (`fastroai/pipelines/pipeline.py`): DAG-based workflow orchestration. Steps declare dependencies, and the executor (`executor.py`) automatically runs independent steps in parallel. Uses `BaseStep` abstract class for step implementations. Supports early termination via `ConversationStatus.INCOMPLETE`.

**@safe_tool** (`fastroai/tools/decorators.py`): Decorator for production-safe AI tools. Adds timeout, exponential backoff retry, and graceful error handling - returns error messages instead of raising exceptions so the AI can handle failures.

**CostCalculator** (`fastroai/usage/calculator.py`): Calculates token costs using integer microcents (1/1,000,000 dollar) to avoid floating-point precision errors in billing. Uses genai-prices for model pricing data with support for custom overrides.

**Tracer Protocol** (`fastroai/tracing/tracer.py`): Protocol-based tracing interface for observability integration. Includes `SimpleTracer` for logging-based tracing and `NoOpTracer` for testing.

### Pipeline Step Patterns

Three ways to define pipeline steps (progressive disclosure):

**1. `@step` decorator** - Concise function-based steps:
```python
from fastroai import step, StepContext

@step(timeout=30.0, retries=2)
async def classify(ctx: StepContext[MyDeps]) -> str:
    response = await ctx.run(classifier_agent, ctx.get_input("text"))
    return response.output
```

**2. `agent.as_step()`** - Single-agent steps:
```python
summarizer = FastroAgent(model="gpt-4o", system_prompt="Summarize.")
summarize_step = summarizer.as_step(lambda ctx: ctx.get_input("document"))
```

**3. `BaseStep` class** - Complex multi-agent steps:
```python
class ResearchStep(BaseStep[MyDeps, Report]):
    classifier = FastroAgent(model="gpt-4o-mini", ...)
    writer = FastroAgent(model="gpt-4o", ...)

    async def execute(self, ctx: StepContext[MyDeps]) -> Report:
        category = await ctx.run(self.classifier, "Classify this")
        report = await ctx.run(self.writer, f"Write about {category.output}")
        return Report(content=report.content)
```

**`ctx.run()` - The key integration point:**
- Passes deps and tracer automatically
- Accumulates usage in `ctx.usage`
- Enforces timeout, retries, cost budget
- Per-call overrides: `await ctx.run(agent, msg, timeout=60.0, retries=3)`

**Config inheritance** (most specific wins):
1. `PipelineConfig` defaults
2. Step class `.config` attribute
3. `step_configs[step_id]` override
4. Per-call `ctx.run(timeout=..., retries=...)` override

### Error Hierarchy

```python
FastroAIError                    # Base for all FastroAI errors
├── PipelineValidationError      # Invalid pipeline config (cycles, unknown steps)
├── StepExecutionError           # Step failed during execution
└── CostBudgetExceededError      # Cost budget was exceeded
```

### Key Design Decisions

- **Stateless agents**: Conversation history is caller-managed, not stored in agent
- **Microcents for billing**: Integer arithmetic prevents precision errors
- **Protocol-based tracing**: Implement `Tracer` protocol for any observability backend
- **Type-safe contexts**: Generic types flow through pipeline steps

## Testing

Tests use `pytest-asyncio` with `asyncio_mode = "auto"`. Mock PydanticAI agents using `model="test"` or `TestModel()`. Strict mypy is disabled for test files.
