# FastroAI 0.4.0 Release Notes

FastroAI 0.4.0 adds enhanced cost tracking with full support for prompt caching, tool usage metrics, and provider-specific usage details. Cost calculations are now up to 18% more accurate when prompt caching is enabled.

## Summary

**What's New for Users:**
- **Cache Token Tracking**: Accurate cost calculation with prompt caching (90% discount for cached tokens)
- **Tool Usage Metrics**: Track `tool_call_count` and `request_count` for agentic behavior monitoring
- **Audio Token Support**: Track audio tokens for multimodal models
- **Provider Details**: Access provider-specific data like reasoning tokens via `usage_details`

**No Breaking Changes** - All new fields have sensible defaults. Existing code works without modification.

## The Problem We Solved

Previously, FastroAI only tracked `input_tokens` and `output_tokens`. When prompt caching was enabled (Anthropic, OpenAI), cached tokens were charged at full price in our calculations, even though providers charge 90% less for cached tokens.

**Example: Personal Finance Assistant with cached system prompt**

| Metric | Before (v0.3.0) | After (v0.4.0) |
|--------|-----------------|----------------|
| Reported Cost | $0.00300 | $0.00246 |
| Accuracy | Overreported by 18% | Accurate |

Now FastroAI extracts cache token counts from the provider and applies the correct discounted rate.

## New Response Fields

`ChatResponse` now includes:

```python
response = await agent.run("Hello!")

# Cache tokens (for prompt caching)
print(response.cache_read_tokens)   # Tokens read from cache (90% cheaper)
print(response.cache_write_tokens)  # Tokens written to cache

# Audio tokens (for multimodal)
print(response.input_audio_tokens)
print(response.output_audio_tokens)

# Request/tool metrics
print(response.request_count)       # API requests made (increases with tool use)
print(response.tool_call_count)     # Number of tool invocations

# Provider-specific details
print(response.usage_details)       # e.g., {"reasoning_tokens": 150} for o1
```

All fields default to 0 or empty, so existing code continues to work.

## Enhanced Cost Calculator

`CostCalculator.calculate_cost()` now accepts cache and audio token parameters:

```python
from fastroai import CostCalculator

calc = CostCalculator()

# Basic usage (unchanged)
cost = calc.calculate_cost("gpt-4o", input_tokens=1000, output_tokens=500)

# With cache tokens (new)
cost = calc.calculate_cost(
    "claude-3-5-sonnet",
    input_tokens=1000,
    output_tokens=500,
    cache_read_tokens=800,  # 800 tokens at 90% discount
)
```

The signature uses keyword-only arguments after `*` for backward compatibility - existing calls work unchanged.

### Pricing Overrides with Cache Tokens

Custom pricing overrides now support cache token rates:

```python
calc = CostCalculator()

# Override with explicit cache rates
calc.add_pricing_override(
    model="my-cached-model",
    input_per_mtok=3.00,
    output_per_mtok=15.00,
    cache_read_per_mtok=0.30,   # 90% discount
    cache_write_per_mtok=3.75,  # 25% premium
)

# Or use default discounts (90% read, 25% write premium)
calc.add_pricing_override(
    model="volume-discount-model",
    input_per_mtok=2.00,
    output_per_mtok=8.00,
)
cost = calc.calculate_cost(
    "volume-discount-model",
    input_tokens=1000,
    output_tokens=0,
    cache_read_tokens=800,  # Applies default 90% discount
)
```

## Pipeline Usage Tracking

`StepUsage` and `PipelineUsage` also include the new fields:

```python
result = await pipeline.execute(input_data, deps)

# Per-step breakdown
for step_id, usage in result.usage.steps.items():
    print(f"{step_id}: {usage.cache_read_tokens} cached tokens")

# Aggregated totals
print(f"Total cached: {result.usage.total_cache_read_tokens}")
print(f"Total tool calls: {result.usage.total_tool_call_count}")
```

## Documentation Updates

- **FastroAgent Guide**: Updated response fields table with cache tokens, request_count, tool_call_count
- **Cost Calculator Guide**: Added "Prompt Caching" section explaining cache token tracking
- **API Reference**: All schemas now use `Field(description=...)` for better auto-generated docs

## Technical Details

**Data Flow:**
1. Provider (Anthropic/OpenAI) returns cache token counts in API response
2. PydanticAI extracts via `genai_prices.extract_usage()`
3. FastroAI extracts from PydanticAI's `RunUsage`
4. `CostCalculator` passes to `genai_prices.calc_price()` for accurate pricing

**Prompt Caching Requirements:**
- **Anthropic**: Prompts >= 1024 tokens
- **OpenAI**: Prompts >= 1024 tokens on gpt-4o models

---

**Full Changelog**: https://github.com/benavlabs/fastroai/compare/v0.3.0...v0.4.0
