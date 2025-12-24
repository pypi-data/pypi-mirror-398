# Implementation Journal: Enhanced Cost Tracking

**Started:** 2025-12-19
**Status:** Planning Complete
**Branch:** `feature/enhanced-cost-tracking` (to be created)

---

## 1. Problem Statement

FastroAI currently captures only `input_tokens` and `output_tokens` from PydanticAI's usage data, missing critical information that affects cost accuracy and observability:

- **Cache tokens** (can reduce costs by 90% on Anthropic)
- **Audio tokens** (multimodal pricing)
- **Request counts** (API call tracking)
- **Tool call counts** (agentic behavior metrics)
- **Provider-specific details** (reasoning tokens for o1, etc.)

This results in **overreported costs** when prompt caching is used and **missing observability** for production monitoring.

---

## 2. Research Findings Summary

### 2.1 Data Available from PydanticAI

PydanticAI's `RunUsage` provides these fields that FastroAI currently ignores:

| Field | Type | Impact |
|-------|------|--------|
| `cache_read_tokens` | `int` | 90% cost reduction on cache hits |
| `cache_write_tokens` | `int` | 25% cost premium on cache writes |
| `input_audio_tokens` | `int` | Different pricing tier |
| `output_audio_tokens` | `int` | Different pricing tier |
| `cache_audio_read_tokens` | `int` | Cached audio pricing |
| `requests` | `int` | API call count |
| `tool_calls` | `int` | Tool invocation count |
| `details` | `dict[str, int]` | Provider-specific (reasoning tokens, etc.) |

### 2.2 genai-prices Support

The `genai_prices` library **already supports** full cost calculation with all token types via `ModelPrice.calc_price()`. FastroAI just needs to pass the data through.

### 2.3 Cost Impact Example

Consider Sarah using our Personal Finance Assistant. She asks:
> "I earn $5,000 monthly and spent $800 on food. Is that too much?"

The agent calls the `financial_analyzer` tool, calculates that 16% is reasonable, and responds with personalized advice. With prompt caching enabled (system prompt cached), here's what happens:

**Token breakdown:**
- System prompt: 200 tokens (cached from previous request)
- User message + history: 50 tokens (uncached)
- Output: 150 tokens

**Current FastroAI calculation (Claude 3.5 Sonnet):**
```
Input:  250 tokens × $3.00/1M  = $0.00075
Output: 150 tokens × $15.00/1M = $0.00225
Total: $0.00300 (3,000 microcents)
```

**Correct calculation (with cache awareness):**
```
Cached input:   200 tokens × $0.30/1M  = $0.00006  (90% discount!)
Uncached input:  50 tokens × $3.00/1M  = $0.00015
Output:         150 tokens × $15.00/1M = $0.00225
Total: $0.00246 (2,460 microcents)
```

**Impact:** FastroAI overreports Sarah's query cost by ~18%. Across thousands of users asking financial questions daily, this adds up to significant phantom costs in your metrics.

---

## 3. Implementation Plan

### Phase 1: Schema Updates (Backward Compatible) ✅

**Goal:** Add new fields to `ChatResponse`, `StepUsage`, and `PipelineUsage` with defaults.

#### Step 1.1: Update `ChatResponse` schema
- [x] Add `cache_read_tokens: int = 0`
- [x] Add `cache_write_tokens: int = 0`
- [x] Add `input_audio_tokens: int = 0`
- [x] Add `output_audio_tokens: int = 0`
- [x] Add `cache_audio_read_tokens: int = 0`
- [x] Add `request_count: int = 1`
- [x] Add `tool_call_count: int = 0`
- [x] Add `usage_details: dict[str, int] = field(default_factory=dict)`

**File:** `fastroai/agent/schemas.py`

#### Step 1.2: Update `StepUsage` schema
- [x] Mirror new fields from `ChatResponse`
- [x] Update `from_chat_response()` factory method
- [x] Update `__add__` to aggregate new fields

**File:** `fastroai/pipelines/schemas.py`

#### Step 1.3: Update `PipelineUsage` schema
- [x] Add aggregated totals for new fields
- [x] Update `from_step_usages()` factory method

**File:** `fastroai/pipelines/schemas.py`

---

### Phase 2: Data Extraction ✅

**Goal:** Extract all available usage data from PydanticAI responses.

#### Step 2.1: Update `_create_response()` in FastroAgent
- [x] Extract `cache_read_tokens` from `usage`
- [x] Extract `cache_write_tokens` from `usage`
- [x] Extract audio token fields
- [x] Extract `requests` count
- [x] Extract `tool_calls` count
- [x] Extract `details` dict

**File:** `fastroai/agent/agent.py`

#### Step 2.2: Update `_create_streaming_response()`
- [x] Same extractions as above for streaming path

**File:** `fastroai/agent/agent.py`

---

### Phase 3: Cost Calculator Enhancement ✅

**Goal:** Pass all token types to genai-prices for accurate cost calculation.

#### Step 3.1: Update `calculate_cost()` signature
- [x] Add optional keyword args for new token types
- [x] Maintain backward compatibility (existing calls still work)

#### Step 3.2: Update cost calculation logic
- [x] Create `genai_prices.Usage` with all token types
- [x] Pass to `calc_price()` for accurate calculation

**File:** `fastroai/usage/calculator.py`

---

### Phase 4: Testing ✅

#### Step 4.1: Unit tests for schemas
- [x] Test new field defaults (existing tests cover this)
- [x] Test `ChatResponse` with all fields
- [x] Test `StepUsage` aggregation with new fields
- [x] Test `PipelineUsage` aggregation

#### Step 4.2: Unit tests for cost calculation
- [x] Test cache token pricing (verify discount applied)
- [x] Test mixed cached/uncached scenarios (Sarah example)
- [x] Test backward compatibility (old signature still works)
- [x] Test audio token parameters

#### Step 4.3: Integration tests
- [x] Test with mock PydanticAI responses containing cache data
- [x] Test pipeline usage aggregation end-to-end (existing tests)

**Files:** `tests/test_agent.py`, `tests/test_usage.py`, `tests/test_pipelines.py`

**New test classes added:**
- `TestCostCalculatorCacheTokens` - 5 tests for cache token pricing
- `TestCostCalculatorAudioTokens` - 2 tests for audio token parameters

---

### Phase 5: Documentation ✅

- [x] Update docstrings for modified classes/methods (using `Field` with descriptions)
- [x] All schemas use `Field(description=...)` instead of docstrings
- [ ] Consider adding usage examples for cache tracking (optional, for future docs)

---

## 4. Architecture Notes

### 4.1 Design Principles to Maintain

1. **Microcents precision** - All costs remain as integers (1 microcent = 1/1,000,000 dollar)
2. **Backward compatibility** - Existing code must continue working
3. **Stateless agents** - No changes to this pattern
4. **Type safety** - Generic types continue flowing through

### 4.2 Data Flow (Enhanced)

```
PydanticAI result.usage() [RunUsage]
    │
    ├─ input_tokens ─────────────┐
    ├─ output_tokens ────────────┤
    ├─ cache_read_tokens ────────┤
    ├─ cache_write_tokens ───────┼──► FastroAgent._create_response()
    ├─ input_audio_tokens ───────┤         │
    ├─ output_audio_tokens ──────┤         ▼
    ├─ cache_audio_read_tokens ──┤    ChatResponse (all fields)
    ├─ requests ─────────────────┤         │
    ├─ tool_calls ───────────────┤         ▼
    └─ details ──────────────────┘    CostCalculator.calculate_cost()
                                           │
                                           ▼
                                      genai_prices.calc_price(Usage(...))
                                           │
                                           ▼
                                      Accurate cost with cache discounts
```

### 4.3 genai-prices Integration

The `genai_prices.Usage` dataclass accepts:
```python
Usage(
    input_tokens=int | None,
    cache_write_tokens=int | None,
    cache_read_tokens=int | None,
    output_tokens=int | None,
    input_audio_tokens=int | None,
    cache_audio_read_tokens=int | None,
    output_audio_tokens=int | None,
)
```

The library's `ModelPrice.calc_price()` then:
1. Subtracts cached tokens from input to get uncached count
2. Applies appropriate rates to each token type
3. Returns `CalcPrice` with `input_price`, `output_price`, `total_price`

### 4.4 Backward Compatibility Strategy

**ChatResponse:** New fields have defaults, existing constructors work.

**CostCalculator.calculate_cost():**
```python
# Before (still works):
calc.calculate_cost("gpt-4o", input_tokens=100, output_tokens=50)

# After (enhanced):
calc.calculate_cost(
    "gpt-4o",
    input_tokens=100,
    output_tokens=50,
    cache_read_tokens=30,  # optional
    cache_write_tokens=20,  # optional
)
```

---

## 5. Progress Log

### 2025-12-19: Research Complete

- [x] Investigated PydanticAI's `RunUsage` class
- [x] Investigated genai-prices `ModelPrice.calc_price()`
- [x] Identified all available but unused fields
- [x] Confirmed genai-prices already supports cache pricing
- [x] Documented cost impact (30% overreporting with caching)
- [x] Created implementation plan

### 2025-12-19: Implementation Complete ✅

- [x] **Phase 1:** Updated all schemas with new fields
  - `ChatResponse` now includes cache tokens, audio tokens, request/tool counts
  - `StepUsage` mirrors ChatResponse fields with aggregation support
  - `PipelineUsage` includes aggregated totals
  - All schemas use `Field(description=...)` pattern
- [x] **Phase 2:** Updated data extraction in agent.py
  - `_create_response()` extracts all usage fields from PydanticAI
  - `_create_streaming_response()` handles same fields for streaming
  - Uses `getattr()` with fallbacks for robustness
- [x] **Phase 3:** Enhanced CostCalculator
  - `calculate_cost()` accepts cache/audio token kwargs
  - Passes all token types to genai-prices for accurate pricing
  - Keyword-only args after `*` for backward compatibility
- [x] **Phase 4:** Tests passing
  - Fixed test mocks to include new usage fields
  - Added 7 new tests for cache/audio token pricing
  - All 215 tests pass (11 skipped)
- [x] **Phase 5:** Documentation complete
  - All schemas documented via Field descriptions

**Quality Checks:** All passing (ruff format, ruff check, mypy, pytest)

---

## 6. Open Questions

1. ~~**PydanticAI tool_calls field:** Research showed this may not be reliably populated. Need to verify behavior.~~
   **RESOLVED (2025-12-19):** Verified that PydanticAI DOES reliably track `tool_calls`. Testing confirmed:
   - `tool_calls` is incremented in `_tool_manager.py:260` after each successful function tool call
   - `requests` count tracks API calls (initial + after tool results)
   - Example: agent with 1 tool call shows `RunUsage(requests=2, tool_calls=1)`

2. **Reasoning tokens:** OpenAI o1 models have `reasoning_tokens` in details. Should we expose this as a first-class field or keep in `usage_details`?
   - **Decision:** Keep in `usage_details` for now. Reasoning tokens are provider-specific and the dict allows flexibility.

3. **Tiered pricing display:** genai-prices supports tiered pricing (e.g., Claude after 200k tokens). Should we expose tier information in responses?
   - **Decision:** Not needed for MVP. The cost calculation already handles tiers internally.

---

## 7. Files Modified

| File | Status | Changes |
|------|--------|---------|
| `fastroai/agent/schemas.py` | ✅ Complete | Added 8 new fields to ChatResponse, all schemas use Field() |
| `fastroai/agent/agent.py` | ✅ Complete | Extract all usage fields in _create_response/_create_streaming_response |
| `fastroai/pipelines/schemas.py` | ✅ Complete | Updated StepUsage + PipelineUsage with aggregation |
| `fastroai/usage/calculator.py` | ✅ Complete | Enhanced calculate_cost() with cache/audio kwargs |
| `tests/test_agent.py` | ✅ Complete | Fixed mocks with new usage fields |
| `tests/test_usage.py` | ✅ Complete | Added TestCostCalculatorCacheTokens + TestCostCalculatorAudioTokens |
| `tests/test_pipelines.py` | ✅ Complete | Existing tests pass with new fields |

---

## 8. References

- PydanticAI usage module: `.venv/lib/python3.12/site-packages/pydantic_ai/usage.py`
- genai-prices types: `.venv/lib/python3.12/site-packages/genai_prices/types.py`
- Current FastroAI agent: `fastroai/agent/agent.py`
- Current cost calculator: `fastroai/usage/calculator.py`
