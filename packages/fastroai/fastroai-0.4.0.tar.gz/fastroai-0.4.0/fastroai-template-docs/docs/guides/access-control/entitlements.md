# Entitlements

Entitlements represent what a user can do in your app. Instead of checking `if user.tier == "pro"`, you check if they have the specific entitlement they need. This sounds like a small difference, but it changes how you think about access control.

## Why Entitlements?

Say you have a Pro user who needs extra API credits for a month. With tier-based checks, you'd need to either upgrade them to Enterprise (wrong tier) or hack something together. With entitlements, you grant them a `CREDIT_GRANT` entitlement and you're done. Their tier stays the same, but they have more credits.

Or imagine a user cancels their subscription. Do they lose access immediately? Get 30 days of read-only access? Keep their data but lose features? With lifecycle handlers, you can customize this behavior without touching your access check code.

## Entitlement Types

There are eight types, and they can be combined freely:

| Type | What it's for |
|------|---------------|
| `SUBSCRIPTION` | Active subscription to a plan |
| `PRODUCT_ACCESS` | One-time purchase (like a course or addon) |
| `CREDIT_GRANT` | Consumable credits (AI tokens, API calls) |
| `FEATURE_UNLOCK` | Access to a specific feature |
| `TIER_ACCESS` | Membership in a tier (free, pro, enterprise) |
| `API_ACCESS` | Permission to use the API programmatically |
| `USAGE_ALLOWANCE` | Quota for specific operations |
| `TEMPORARY_ACCESS` | Time-limited access (trials, promotions) |

A user might have a `SUBSCRIPTION` entitlement from their monthly plan, a `CREDIT_GRANT` from a promotion, and a `FEATURE_UNLOCK` from an enterprise contract. They all stack.

## Checking Access

The basic pattern is straightforward:

```python
from src.modules.entitlement.service import EntitlementService
from src.modules.entitlement.schemas import EntitlementCheckRequest
from src.modules.entitlement.enums import EntitlementType

entitlement_service = EntitlementService()

check = await entitlement_service.check_entitlement(
    EntitlementCheckRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.FEATURE_UNLOCK,
    ),
    db,
)

if check.has_access:
    # Show the feature
    ...
```

The response tells you more than just yes/no. You get `total_available_quantity` for consumable entitlements, `expires_at` for the earliest expiration, and any `limitations` from the entitlement metadata.

### Checking Quantity

For consumable entitlements like credits, you often want to check if the user has enough before starting an operation:

```python
check = await entitlement_service.check_entitlement(
    EntitlementCheckRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.CREDIT_GRANT,
        credit_type="ai_tokens",
        required_quantity=1000,
    ),
    db,
)

if not check.has_access:
    raise InsufficientCreditsError("You need at least 1000 tokens for this operation")
```

## Granting Entitlements

Most entitlements are granted automatically when users subscribe or purchase something. The Stripe webhook handlers take care of this.

But sometimes you need to grant entitlements manually. Maybe you're running a promotion, compensating a user for an issue, or setting up an enterprise deal.

### Through the Admin API

Superusers can grant entitlements via the API:

```bash
POST /api/v1/entitlements/grant
Content-Type: application/json

{
    "user_id": 123,
    "entitlement_type": "credit_grant",
    "credit_type": "ai_tokens",
    "quantity_granted": 10000,
    "grant_reason": "promotion",
    "notes": "Compensation for downtime on 2024-01-15"
}
```

The `grant_reason` helps you track why entitlements exist. You can use `promotion`, `bonus`, `trial`, `manual`, or `enterprise_contract` depending on the situation.

### In Your Code

```python
from src.modules.entitlement.schemas import EntitlementGrantRequest
from src.modules.entitlement.enums import EntitlementType, GrantReason

await entitlement_service.grant_entitlement(
    EntitlementGrantRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.CREDIT_GRANT,
        credit_type="ai_tokens",
        quantity_granted=5000,
        grant_reason=GrantReason.BONUS,
        notes="Referral bonus",
    ),
    db,
)
```

### Grant Request Parameters

The `EntitlementGrantRequest` has several parameters depending on what you're granting:

**Required for all grants:**

| Parameter | Description |
|-----------|-------------|
| `user_id` | Who gets the entitlement |
| `entitlement_type` | One of the eight types |
| `grant_reason` | Why it's being granted (for audit trail) |

**Type-specific parameters:**

| Parameter | Required for | Example |
|-----------|--------------|---------|
| `subscription_id` | `SUBSCRIPTION` | Link to Stripe subscription record |
| `product_id` | `PRODUCT_ACCESS` | Link to purchased product |
| `tier_id` | `TIER_ACCESS` | Link to tier record |
| `credit_type` | `CREDIT_GRANT` | `"ai_tokens"`, `"api_calls"`, etc. |

**Optional parameters:**

| Parameter | What it does |
|-----------|--------------|
| `expires_at` | When the entitlement expires. `None` means permanent. |
| `granted_at` | When to activate. Defaults to now, but you can schedule future grants. |
| `quantity_granted` | For consumable entitlements. `None` means unlimited. |
| `consumption_type` | `NONE`, `DECREMENTAL`, `RENEWABLE`, or `ACCUMULATIVE` |
| `reference_id` | External ID (like a Stripe subscription ID) for tracking |
| `cost_microcents` | What was paid, for reporting |
| `notes` | Admin notes for context |
| `entitlement_metadata` | Arbitrary JSON for rate limits, feature flags, etc. |

**Examples for different scenarios:**

```python
# Grant a 14-day trial
await entitlement_service.grant_entitlement(
    EntitlementGrantRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.TEMPORARY_ACCESS,
        grant_reason=GrantReason.TRIAL,
        expires_at=datetime.now(UTC) + timedelta(days=14),
        entitlement_metadata={"trial_type": "full_access"},
    ),
    db,
)

# Grant monthly API quota that resets
await entitlement_service.grant_entitlement(
    EntitlementGrantRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.USAGE_ALLOWANCE,
        grant_reason=GrantReason.SUBSCRIPTION,
        reference_id="sub_abc123",
        quantity_granted=10000,
        consumption_type=ConsumptionType.RENEWABLE,
        entitlement_metadata={"reset_day": 1},  # First of each month
    ),
    db,
)

# Grant lifetime product access
await entitlement_service.grant_entitlement(
    EntitlementGrantRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.PRODUCT_ACCESS,
        product_id=42,
        grant_reason=GrantReason.PURCHASE,
        reference_id="pi_xyz789",
        cost_microcents=4900000,  # $49.00
        # No expires_at = permanent
    ),
    db,
)
```

## Consuming Credits

When a user spends credits (like making an AI request), you need to deduct from their balance:

```python
from src.modules.entitlement.schemas import EntitlementConsumptionRequest

usage_records = await entitlement_service.consume_entitlement(
    EntitlementConsumptionRequest(
        user_id=user.id,
        entitlement_type=EntitlementType.CREDIT_GRANT,
        credit_type="ai_tokens",
        quantity_to_consume=500,
        usage_context={"model": "gpt-4", "conversation_id": 123},
    ),
    db,
)
```

The service handles the bookkeeping: it finds the oldest entitlements first (FIFO), spreads consumption across multiple grants if needed, and creates usage records for your audit trail. If there aren't enough credits, it raises `InsufficientCreditsError`.

### Consumption Types

Not all entitlements work the same way:

- **`NONE`** - Feature access, nothing to consume
- **`DECREMENTAL`** - Credits that get used up
- **`RENEWABLE`** - Resets periodically (like "1000 requests per month")
- **`ACCUMULATIVE`** - Unused credits roll over

## Credit Dependencies

Writing check-then-consume logic in every route gets repetitive. FastroAI provides dependency factories that handle this pattern for you.

For a fixed cost (say, 10 credits per document analysis):

```python
from src.infrastructure.credit_consumption import require_credits
from src.modules.credits.enums import CreditType

ConsumeDocumentCredits = require_credits(
    credit_type=CreditType.DOCUMENT_ANALYSIS,
    cost=10,
    description="Document Analysis"
)

@router.post("/analyze")
async def analyze_document(
    document: Document,
    credit_info: dict = Depends(ConsumeDocumentCredits),
):
    # If we get here, the user had 10 credits and they've been consumed.
    # If they didn't have enough, they got HTTP 402 before this code ran.
    return await process_document(document)
```

The dependency checks the balance and consumes credits before your handler runs. If the user doesn't have enough credits, it returns HTTP 402 with details about what's needed.

When the cost varies (like tier-based pricing), use a calculator function:

```python
from src.infrastructure.credit_consumption import require_variable_credits

def calculate_ai_message_cost(request: Request, user: dict) -> int:
    tier = user.get("tier_name", "free")
    return {"enterprise": 1, "pro": 2, "starter": 3, "free": 5}.get(tier, 5)

ConsumeAICredits = require_variable_credits(
    credit_type=CreditType.AI_TOKENS,
    cost_calculator=calculate_ai_message_cost,
    description="AI Chat Message"
)

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    message: MessageSend,
    credit_info: dict = Depends(ConsumeAICredits),
):
    response = await conversation_service.send_message(...)

    # You can include the credit info in your response
    response["credit_transaction"] = {
        "credits_used": credit_info["credits_consumed"],
        "remaining_balance": credit_info["remaining_balance"],
    }
    return response
```

The `credit_info` dict gives you `credits_consumed`, `remaining_balance`, `transaction_id`, and `credit_type` so you can include this information in your API responses.

You can build similar dependencies for feature checks too. The pattern is the same: do the check in the dependency, raise an appropriate HTTP error if it fails, and let your route handler focus on business logic.

## Revoking Entitlements

When a subscription is cancelled or a refund is issued, you'll want to revoke the associated entitlements:

```python
# Revoke a specific entitlement by ID
await entitlement_service.revoke_entitlement(
    entitlement_id=123,
    db=db,
    reason="Subscription cancelled",
)

# Revoke all entitlements from a Stripe subscription
await entitlement_service.revoke_entitlements_by_reference(
    reference_id="sub_abc123",
    db=db,
    reason="Refund processed",
)
```

Revocation is a soft delete. The entitlement record stays in the database for audit purposes, but it's marked as inactive.

## Lifecycle Handlers

What happens when a subscription is cancelled? The default behavior is to revoke the entitlements and that's it. But you might want something different:

- Freemium apps typically downgrade users to a free tier
- Enterprise apps might give 30 days of read-only access
- Some apps let users keep their data but disable features

Lifecycle handlers let you customize this without modifying the entitlement service.

### Switching Handlers

```python
# Use the freemium handler (grants free tier after cancellation)
entitlement_service = EntitlementService(lifecycle_handler_name="freemium")
```

### Creating Your Own Handler

If the built-in handlers don't fit your needs, create one in `backend/src/modules/entitlement/lifecycle_handlers/`:

```python
from .base import EntitlementLifecycleHandler

class GracePeriodHandler(EntitlementLifecycleHandler):
    def __init__(self, entitlement_service):
        self.entitlement_service = entitlement_service

    async def handle_subscription_cancelled(
        self, subscription_id: str, db, **context
    ) -> list[UserEntitlementRead]:
        # Revoke the subscription entitlements
        revoked = await self.entitlement_service.revoke_entitlements_by_reference(
            subscription_id, db, reason="Subscription cancelled"
        )

        # But give them 14 days of temporary access
        user_id = context.get("user_id")
        if user_id:
            await self.entitlement_service.grant_entitlement(
                EntitlementGrantRequest(
                    user_id=user_id,
                    entitlement_type=EntitlementType.TEMPORARY_ACCESS,
                    expires_at=datetime.now(UTC) + timedelta(days=14),
                    grant_reason=GrantReason.SUBSCRIPTION_CANCELLED,
                ),
                db,
            )

        return revoked
```

Then register it in `lifecycle_handlers/provider.py`.

## Getting a User Summary

To see everything a user has access to:

```python
summary = await entitlement_service.get_user_summary(user_id=123, db=db)

# summary.active_entitlements - count of active entitlements
# summary.has_active_subscription - whether they have a paid subscription
# summary.total_credits_available - {"ai_tokens": 5000, "api_calls": 100}
# summary.total_credits_used - {"ai_tokens": 2300, "api_calls": 45}
```

## Admin Endpoints

All entitlement endpoints require superuser access:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/entitlements/users/{user_id}` | GET | List user's entitlements |
| `/api/v1/entitlements/users/{user_id}/summary` | GET | Get summary with credit balances |
| `/api/v1/entitlements/grant` | POST | Grant a new entitlement |
| `/api/v1/entitlements/{id}` | GET | Get entitlement details |
| `/api/v1/entitlements/{id}` | DELETE | Revoke an entitlement |

## Key Files

| Component | Location |
|-----------|----------|
| Entitlement service | `backend/src/modules/entitlement/service.py` |
| Types and enums | `backend/src/modules/entitlement/enums.py` |
| Database model | `backend/src/modules/entitlement/models.py` |
| Lifecycle handlers | `backend/src/modules/entitlement/lifecycle_handlers/` |
| API endpoints | `backend/src/interfaces/api/v1/entitlements.py` |

---

[← Access Control Overview](index.md){ .md-button } [API Keys →](api-keys.md){ .md-button .md-button--primary }
